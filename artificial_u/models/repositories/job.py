"""
Job repository implementing enqueue, reservation (skip locked), state transitions, and sweeping.
"""

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, asc, desc, func, select, text, update

from artificial_u.models.database import JobModel
from artificial_u.models.repositories.base import BaseRepository


class JobRepository(BaseRepository):
    def create(
        self,
        *,
        kind: str,
        payload: Dict[str, Any],
        priority: int = 0,
        run_after: Optional[dt.datetime] = None,
        max_attempts: int = 5,
    ) -> JobModel:
        run_after = run_after or dt.datetime.now()
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

            stmt = stmt.order_by(desc(JobModel.created_at)).limit(limit)
            return list(session.execute(stmt).scalars())

    def reserve_one_skip_locked(self) -> Optional[JobModel]:
        with self.get_session() as session:
            stmt = (
                select(JobModel)
                .where(and_(JobModel.status == "queued", JobModel.run_after <= func.now()))
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
                .values(status="running", attempts=JobModel.attempts + 1, updated_at=func.now())
            )
            session.commit()
            return self.get(row.id)

    def reserve_one_skip_locked_atomic(self) -> Optional[JobModel]:
        """
        Atomically reserve a single queued job using a CTE and SKIP LOCKED.
        Returns the reserved JobModel or None if none available.
        """
        with self.get_session() as session:
            sql = text(
                """
                WITH cte AS (
                  SELECT id
                  FROM jobs
                  WHERE status = 'queued' AND run_after <= now()
                  ORDER BY priority DESC, id
                  FOR UPDATE SKIP LOCKED
                  LIMIT 1
                )
                UPDATE jobs j
                SET status = 'running', updated_at = now(), attempts = attempts + 1
                FROM cte
                WHERE j.id = cte.id
                RETURNING j.id;
                """
            )
            result = session.execute(sql).first()
            session.commit()
            if not result:
                return None
            job_id = result[0]
            return self.get(job_id)

    def mark_done(self, job_id: int, result: Dict[str, Any]) -> None:
        with self.get_session() as session:
            session.execute(
                update(JobModel)
                .where(JobModel.id == job_id)
                .values(status="done", result=result, updated_at=func.now())
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
    ) -> None:
        with self.get_session() as session:
            if attempts >= max_attempts:
                session.execute(
                    update(JobModel)
                    .where(JobModel.id == job_id)
                    .values(
                        status="failed",
                        last_error=last_error[:2000],
                        updated_at=func.now(),
                    )
                )
            else:
                delay_seconds = delay_seconds or 0
                next_time = func.now() + text(f"make_interval(secs => {int(delay_seconds)} )")
                session.execute(
                    update(JobModel)
                    .where(JobModel.id == job_id)
                    .values(
                        status="queued",
                        last_error=last_error[:2000],
                        run_after=next_time,
                        updated_at=func.now(),
                    )
                )
            session.commit()

    def mark_cancelled(self, job_id: int) -> None:
        with self.get_session() as session:
            session.execute(
                update(JobModel)
                .where(JobModel.id == job_id)
                .values(status="cancelled", updated_at=func.now())
            )
            session.commit()

    def summary_counts(self) -> List[Tuple[str, int]]:
        with self.get_session() as session:
            rows = session.execute(
                select(JobModel.status, func.count()).group_by(JobModel.status)
            ).all()
            return [(r[0], r[1]) for r in rows]

    def sweep_stuck(self, *, visibility_timeout_seconds: int) -> int:
        with self.get_session() as session:
            cutoff = func.now() - text(f"make_interval(secs => {int(visibility_timeout_seconds)})")
            result = session.execute(
                update(JobModel)
                .where(and_(JobModel.status == "running", JobModel.updated_at < cutoff))
                .values(status="queued", updated_at=func.now())
            )
            session.commit()
            return result.rowcount or 0
