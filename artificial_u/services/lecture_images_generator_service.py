import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

import httpx

from artificial_u.services.http_client import get_shared_async_client
from artificial_u.services.image_service import ImageService
from artificial_u.services.storage_service import StorageService


class LectureImagesGeneratorService:
    """
    Generate synced lecture slideshow images (admin-triggered).

    v1 intentionally uses a simple scheduling strategy: slots are distributed
    evenly across the lecture duration (derived from the forced-alignment
    timeline when available). This is good enough to iterate on prompting and
    UX; the slot-to-text mapping algorithm can be upgraded later without
    changing storage format.
    """

    _timeline_locks: Dict[str, asyncio.Lock] = {}

    def __init__(
        self,
        lecture_service: Any,
        course_service: Any,
        topic_service: Any,
        professor_service: Any,
        storage_service: Optional[StorageService] = None,
        image_service: Optional[ImageService] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.lecture_service = lecture_service
        self.course_service = course_service
        self.topic_service = topic_service
        self.professor_service = professor_service
        self.storage_service = storage_service or StorageService(logger=logger)
        self.http_client = http_client or get_shared_async_client()
        self.image_service = image_service or ImageService(
            self.storage_service,
            http_client=self.http_client,
        )
        self.logger = logger or logging.getLogger(__name__)

    async def _fetch_timeline(self, url: str) -> Dict[str, Any]:
        resp = await self.http_client.get(url, timeout=30.0)
        resp.raise_for_status()
        return resp.json()

    def _estimate_duration_from_timeline(self, timeline: Dict[str, Any]) -> float:
        events = timeline.get("events") or []
        if not events:
            return 0.0
        # timeline uses seconds (floats)
        return float(max((e.get("end") or 0.0) for e in events))

    def _chunk_text(self, text: str, n: int) -> List[str]:
        # Paragraph-first chunking, then fallback to word chunking.
        paragraphs = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
        if not paragraphs:
            return [""] * n

        total_words = sum(len(p.split()) for p in paragraphs) or 1
        target_words = max(80, total_words // max(1, n))

        chunks: List[str] = []
        buf: List[str] = []
        buf_words = 0

        for p in paragraphs:
            w = len(p.split())
            if buf and buf_words + w > target_words and len(chunks) < n - 1:
                chunks.append("\n\n".join(buf).strip())
                buf = []
                buf_words = 0

            buf.append(p)
            buf_words += w

        if buf:
            chunks.append("\n\n".join(buf).strip())

        # Normalize length to exactly n.
        if len(chunks) < n:
            chunks.extend([""] * (n - len(chunks)))
        elif len(chunks) > n:
            # Merge extras into the last chunk.
            head = chunks[: n - 1]
            tail = "\n\n".join(chunks[n - 1 :]).strip()
            chunks = head + [tail]

        return chunks

    def _timeline_lock(self, object_key: str) -> asyncio.Lock:
        lock = self._timeline_locks.get(object_key)
        if lock is None:
            lock = asyncio.Lock()
            self._timeline_locks[object_key] = lock
        return lock

    async def _load_images_timeline(self, object_key: str) -> Dict[str, Any]:
        data, _ = await self.storage_service.download_lecture_file(object_key)
        if not data:
            raise RuntimeError(f"Lecture images timeline not found: {object_key}")
        return json.loads(data.decode("utf-8"))

    async def _upload_images_timeline(
        self, object_key: str, images_timeline: Dict[str, Any]
    ) -> Optional[str]:
        timeline_bytes = json.dumps(images_timeline, ensure_ascii=False).encode("utf-8")
        success, url = await self.storage_service.upload_timeline_file(
            file_data=timeline_bytes,
            object_name=object_key,
            content_type="application/json",
        )
        if not success:
            raise RuntimeError("Failed to upload lecture images timeline")
        return url

    def _slot_for_index(
        self, images_timeline: Dict[str, Any], slot_idx: int
    ) -> Optional[Dict[str, Any]]:
        for slot in images_timeline.get("slots") or []:
            if int(slot.get("index", -1)) == int(slot_idx):
                return slot
        return None

    async def _update_slot(
        self,
        object_key: str,
        slot_idx: int,
        *,
        batch_id: Optional[str],
        status: str,
        url: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self._timeline_lock(object_key):
            images_timeline = await self._load_images_timeline(object_key)
            if batch_id and images_timeline.get("batch_id") != batch_id:
                return images_timeline

            slot = self._slot_for_index(images_timeline, slot_idx)
            if slot is None:
                raise ValueError(f"Slot {slot_idx} not found in lecture images timeline")

            slot["status"] = status
            if url is not None:
                slot["url"] = url
            if error is not None:
                slot["error"] = error[:500]
            elif "error" in slot:
                slot.pop("error", None)

            await self._upload_images_timeline(object_key, images_timeline)
            return images_timeline

    async def plan_lecture_images(
        self,
        lecture_id: int,
        *,
        interval_sec: int = 30,
        min_images: int = 6,
        max_images: int = 40,
        aspect_ratio: str = "1:1",
        model_name_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        lecture = self.lecture_service.get_lecture(lecture_id)
        if not lecture.timeline_url:
            raise ValueError("Lecture timeline_url is required before generating lecture images")
        if not lecture.content:
            raise ValueError("Lecture content is required before generating lecture images")

        course = self.course_service.get_course(lecture.course_id)
        topic = self.topic_service.get_topic(lecture.topic_id)

        timeline = await self._fetch_timeline(lecture.timeline_url)
        duration = float(getattr(lecture, "duration", 0) or 0)
        if duration <= 0:
            duration = self._estimate_duration_from_timeline(timeline)

        if duration <= 0:
            # Conservative fallback to 20 minutes
            duration = 20 * 60

        total = int(round(duration / max(1, interval_sec)))
        total = max(min_images, min(max_images, total))

        chunks = self._chunk_text(lecture.content, total)

        resolved_model_name = model_name_override or getattr(self.image_service, "model_name", None)
        batch_id = str(uuid.uuid4())

        # Build scaffold json and upload it first.
        slots: List[Dict[str, Any]] = []
        for i in range(total):
            start = (duration * i) / total
            end = (duration * (i + 1)) / total
            preview = (chunks[i] or "").replace("\n", " ").strip()[:180]
            slots.append(
                {
                    "index": i,
                    "start": round(start, 3),
                    "end": round(end, 3),
                    "chunk_preview": preview,
                    "url": None,
                    "status": "pending",
                    "model": resolved_model_name,
                }
            )

        images_timeline = {
            "version": 1,
            "batch_id": batch_id,
            "lecture_id": lecture_id,
            "aspect_ratio": aspect_ratio,
            "model": resolved_model_name,
            "slots": slots,
        }

        course_code = getattr(course, "code", str(getattr(course, "id", "course")))
        week = int(getattr(topic, "week", 1))
        order = int(getattr(topic, "order", 1))

        object_key = self.storage_service.generate_lecture_images_timeline_key(
            course_code=str(course_code),
            week_number=week,
            lecture_order=order,
        )

        images_timeline_url = await self._upload_images_timeline(object_key, images_timeline)
        if not images_timeline_url:
            raise RuntimeError("Failed to upload lecture images timeline")

        # Persist URL immediately so UI can show placeholders.
        self.lecture_service.update_lecture(
            lecture_id=lecture_id,
            update_data={"images_timeline_url": images_timeline_url},
        )

        slide_payloads: List[Dict[str, Any]] = []
        for i in range(total):
            slide_payloads.append(
                {
                    "lecture_id": lecture_id,
                    "topic_id": getattr(lecture, "topic_id", None),
                    "batch_id": batch_id,
                    "slot_idx": i,
                    "total": total,
                    "object_key": object_key,
                    "images_timeline_url": images_timeline_url,
                    "aspect_ratio": aspect_ratio,
                    "model_name_override": model_name_override,
                    "chunk_text": chunks[i],
                    "previous_chunk_text": chunks[i - 1] if i > 0 else None,
                }
            )

        return {
            "lecture_id": lecture_id,
            "images_timeline_url": images_timeline_url,
            "object_key": object_key,
            "batch_id": batch_id,
            "total": total,
            "planned": total,
            "slide_payloads": slide_payloads,
        }

    async def generate_lecture_slide(
        self,
        lecture_id: int,
        *,
        slot_idx: int,
        object_key: str,
        batch_id: Optional[str],
        chunk_text: str,
        previous_chunk_text: Optional[str] = None,
        aspect_ratio: str = "1:1",
        model_name_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        lecture = self.lecture_service.get_lecture(lecture_id)
        if not lecture:
            raise ValueError(f"Lecture {lecture_id} not found")

        course = self.course_service.get_course(lecture.course_id)
        topic = self.topic_service.get_topic(lecture.topic_id)
        professor_id = getattr(course, "professor_id", None)
        if not professor_id:
            raise ValueError(f"Course {course.id} has no professor for lecture image generation")
        professor = self.professor_service.get_professor(professor_id)
        if not professor:
            raise ValueError(f"Professor {professor_id} not found for lecture image generation")

        images_timeline = await self._load_images_timeline(object_key)
        if batch_id and images_timeline.get("batch_id") != batch_id:
            return {
                "lecture_id": lecture_id,
                "slot_idx": slot_idx,
                "status": "skipped",
                "reason": "stale_batch",
            }

        slot = self._slot_for_index(images_timeline, slot_idx)
        if slot is None:
            raise ValueError(f"Slot {slot_idx} not found in lecture images timeline")
        if slot.get("url") and slot.get("status") == "done":
            return {
                "lecture_id": lecture_id,
                "slot_idx": slot_idx,
                "status": "skipped",
                "reason": "already_done",
                "url": slot.get("url"),
            }

        course_code = getattr(course, "code", str(getattr(course, "id", "course")))
        week = int(getattr(topic, "week", 1))
        order = int(getattr(topic, "order", 1))
        image_key = self.storage_service.generate_lecture_image_key(
            course_code=str(course_code),
            week_number=week,
            lecture_order=order,
            slot_idx=slot_idx,
        )

        if await self.storage_service.object_exists(self.storage_service.images_bucket, image_key):
            url = self.storage_service.get_file_url(self.storage_service.images_bucket, image_key)
            await self._update_slot(object_key, slot_idx, batch_id=batch_id, status="done", url=url)
            return {"lecture_id": lecture_id, "slot_idx": slot_idx, "status": "done", "url": url}

        await self._update_slot(object_key, slot_idx, batch_id=batch_id, status="running")

        latest_timeline = await self._load_images_timeline(object_key)
        previous_slide_url = None
        previous_slot = self._slot_for_index(latest_timeline, slot_idx - 1)
        if previous_slot:
            previous_slide_url = previous_slot.get("url")

        slide_url = await self.image_service.generate_lecture_slide_image(
            professor=professor,
            course=course,
            week_number=week,
            lecture_order=order,
            lecture_summary=getattr(lecture, "summary", None),
            chunk_text=chunk_text,
            previous_chunk_text=previous_chunk_text,
            previous_slide_url=previous_slide_url,
            slot_idx=slot_idx,
            aspect_ratio=aspect_ratio,
            model_name_override=model_name_override,
        )

        if slide_url:
            await self._update_slot(
                object_key, slot_idx, batch_id=batch_id, status="done", url=slide_url
            )
            return {
                "lecture_id": lecture_id,
                "slot_idx": slot_idx,
                "status": "done",
                "url": slide_url,
            }

        await self._update_slot(
            object_key,
            slot_idx,
            batch_id=batch_id,
            status="failed",
            error="image_generation_returned_no_url",
        )
        return {
            "lecture_id": lecture_id,
            "slot_idx": slot_idx,
            "status": "failed",
        }
