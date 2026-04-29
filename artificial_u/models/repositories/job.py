"""
Job repository implementing enqueue, reservation (skip locked), state transitions, and sweeping.
"""

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, asc, desc, func, select, text, update

from artificial_u.models.database import JobModel
from artificial_u.models.repositories.base import BaseRepository


class JobRepository(BaseRepository):
    @staticmethod
    def _now() -> dt.datetime:
        return dt.datetime.now()

    def create(
        self,
        *,
        kind: str,
        payload: Dict[str, Any],
        priority: int = 0,
        run_after: Optional[dt.datetime] = None,
        max_attempts: int = 2,
    ) -> JobModel:
        run_after = run_after or self._now()
        with self.get_session() as session:
            job = JobModel(
                kind=kind,
                payload=payload,
                status="queued",
                priority=priority,
                run_after=run_after,
                max_attempts=max_attempts,
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def get(self, job_id: int) -> Optional[JobModel]:
        with self.get_session() as session:
            return session.get(JobModel, job_id)

    def list(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        kind: Optional[str] = None,
        lecture_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        course_id: Optional[int] = None,
    ) -> List[JobModel]:
        with self.get_session() as session:
            stmt = select(JobModel)
            if status:
                stmt = stmt.where(JobModel.status == status)
            if kind:
                stmt = stmt.where(JobModel.kind == kind)

            # JSONB payload filters (best-effort on Postgres)
            if lecture_id is not None:
                from sqlalchemy import Integer, cast

                stmt = stmt.where(
                    cast(JobModel.payload["lecture_id"].astext, Integer) == int(lecture_id)
                )

            if topic_id is not None:
                from sqlalchemy import Integer, cast, or_

                stmt = stmt.where(
                    or_(
                        cast(JobModel.payload["topic_id"].astext, Integer) == int(topic_id),
                        cast(JobModel.payload["partial_attributes"]["topic_id"].astext, Integer)
                        == int(topic_id),
                    )
                )

            if course_id is not None:
                from sqlalchemy import Integer, cast, or_

                stmt = stmt.where(
                    or_(
                        cast(JobModel.payload["course_id"].astext, Integer) == int(course_id),
                        cast(JobModel.payload["partial_attributes"]["course_id"].astext, Integer)
                        == int(course_id),
                    )
                )

            stmt = stmt.order_by(desc(JobModel.created_at)).limit(limit)
            return list(session.execute(stmt).scalars())

    def reserve_one_skip_locked(self) -> Optional[JobModel]:
        now = self._now()
        with self.get_session() as session:
            stmt = (
                select(JobModel)
                .where(and_(JobModel.status == "queued", JobModel.run_after <= now))
                .order_by(desc(JobModel.priority), asc(JobModel.id))
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            row = session.execute(stmt).scalars().first()
            if not row:
                return None
            # transition to running and increment attempts
            session.execute(
                update(JobModel)
                .where(JobModel.id == row.id)
                .values(status="running", attempts=JobModel.attempts + 1, updated_at=now)
            )
            session.commit()
            return self.get(row.id)

    def reserve_one_skip_locked_atomic(self) -> Optional[JobModel]:
        """
        Atomically reserve a single queued job using a CTE and SKIP LOCKED.
        Returns the reserved JobModel or None if none available.
        """
        now = self._now()
        with self.get_session() as session:
            sql = text("""
                WITH cte AS (
                  SELECT id
                  FROM jobs
                  WHERE status = 'queued' AND run_after <= :now
                  ORDER BY priority DESC, id
                  FOR UPDATE SKIP LOCKED
                  LIMIT 1
                )
                UPDATE jobs j
                SET status = 'running', updated_at = :now, attempts = attempts + 1
                FROM cte
                WHERE j.id = cte.id
                RETURNING j.id;
                """)
            result = session.execute(sql, {"now": now}).first()
            session.commit()
            if not result:
                return None
            job_id = result[0]
            return self.get(job_id)

    def mark_done(self, job_id: int, result: Dict[str, Any]) -> None:
        now = self._now()
        with self.get_session() as session:
            session.execute(
                update(JobModel)
                .where(JobModel.id == job_id)
                .values(status="done", result=result, updated_at=now)
            )
            session.commit()

    def mark_failed_or_retry(
        self,
        job_id: int,
        attempts: int,
        max_attempts: int,
        *,
        last_error: str,
        delay_seconds: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = self._now()
        with self.get_session() as session:
            if attempts >= max_attempts:
                values: Dict[str, Any] = {
                    "status": "failed",
                    "last_error": last_error[:2000],
                    "updated_at": now,
                }
                if result is not None:
                    values["result"] = result
                session.execute(update(JobModel).where(JobModel.id == job_id).values(**values))
            else:
                delay_seconds = delay_seconds or 0
                next_time = now + dt.timedelta(seconds=delay_seconds)
                qvalues: Dict[str, Any] = {
                    "status": "queued",
                    "last_error": last_error[:2000],
                    "run_after": next_time,
                    "updated_at": now,
                }
                if result is not None:
                    qvalues["result"] = result
                session.execute(update(JobModel).where(JobModel.id == job_id).values(**qvalues))
            session.commit()

    def mark_cancelled(self, job_id: int) -> None:
        now = self._now()
        with self.get_session() as session:
            session.execute(
                update(JobModel)
                .where(JobModel.id == job_id)
                .values(status="cancelled", updated_at=now)
            )
            session.commit()

    def summary_counts(self) -> List[Tuple[str, int]]:
        with self.get_session() as session:
            rows = session.execute(
                select(JobModel.status, func.count()).group_by(JobModel.status)
            ).all()
            return [(r[0], r[1]) for r in rows]

    def telemetry_summary(self) -> Dict[str, Any]:
        """
        Lightweight queue health snapshot for CloudWatch custom metrics.

        Returns:
          - counts by status
          - avg_wait_seconds for queued jobs (now - created_at)
          - failed_last_hour count
        """
        now = self._now()
        with self.get_session() as session:
            counts_rows = session.execute(
                select(JobModel.status, func.count()).group_by(JobModel.status)
            ).all()
            counts: Dict[str, int] = {str(s): int(c) for s, c in counts_rows}

            avg_wait = session.execute(
                select(func.avg(func.extract("epoch", now - JobModel.created_at))).where(
                    JobModel.status == "queued"
                )
            ).scalar()
            try:
                avg_wait_seconds = float(avg_wait) if avg_wait is not None else 0.0
            except Exception:
                avg_wait_seconds = 0.0

            failed_last_hour = session.execute(
                select(func.count())
                .select_from(JobModel)
                .where(
                    and_(
                        JobModel.status == "failed",
                        JobModel.updated_at >= now - dt.timedelta(hours=1),
                    )
                )
            ).scalar()
            failed_last_hour_count = int(failed_last_hour or 0)

            return {
                "counts": counts,
                "avg_wait_seconds": avg_wait_seconds,
                "failed_last_hour": failed_last_hour_count,
            }

    def sweep_stuck(self, *, visibility_timeout_seconds: int) -> int:
        now = self._now()
        with self.get_session() as session:
            cutoff = now - dt.timedelta(seconds=visibility_timeout_seconds)
            result = session.execute(
                update(JobModel)
                .where(and_(JobModel.status == "running", JobModel.updated_at < cutoff))
                .values(status="queued", updated_at=now)
            )
            session.commit()
            return result.rowcount or 0
