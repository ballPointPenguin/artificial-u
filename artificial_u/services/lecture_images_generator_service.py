import json
import logging
from typing import Any, Dict, List, Optional

import httpx

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

    def __init__(
        self,
        lecture_service: Any,
        course_service: Any,
        topic_service: Any,
        professor_service: Any,
        storage_service: Optional[StorageService] = None,
        image_service: Optional[ImageService] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.lecture_service = lecture_service
        self.course_service = course_service
        self.topic_service = topic_service
        self.professor_service = professor_service
        self.storage_service = storage_service or StorageService(logger=logger)
        self.image_service = image_service or ImageService(self.storage_service)
        self.logger = logger or logging.getLogger(__name__)

    async def _fetch_timeline(self, url: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30.0)
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

    async def generate_lecture_images(
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
        professor = None
        if getattr(course, "professor_id", None):
            professor = self.professor_service.get_professor(course.professor_id)

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

        timeline_bytes = json.dumps(images_timeline, ensure_ascii=False).encode("utf-8")
        success, images_timeline_url = await self.storage_service.upload_timeline_file(
            file_data=timeline_bytes,
            object_name=object_key,
            content_type="application/json",
        )
        if not success or not images_timeline_url:
            raise RuntimeError("Failed to upload lecture images timeline")

        # Persist URL immediately so UI can show placeholders.
        self.lecture_service.update_lecture(
            lecture_id=lecture_id,
            update_data={"images_timeline_url": images_timeline_url},
        )

        # Generate slides sequentially.
        prev_slide_url: Optional[str] = None
        done = 0
        for i in range(total):
            slots[i]["status"] = "running"
            timeline_bytes = json.dumps(images_timeline, ensure_ascii=False).encode("utf-8")
            await self.storage_service.upload_timeline_file(
                file_data=timeline_bytes,
                object_name=object_key,
                content_type="application/json",
            )

            slide_url = await self.image_service.generate_lecture_slide_image(
                professor=professor or course,  # fallback; prompt builder tolerates missing attrs
                course=course,
                week_number=week,
                lecture_order=order,
                lecture_summary=getattr(lecture, "summary", None),
                chunk_text=chunks[i],
                previous_chunk_text=chunks[i - 1] if i > 0 else None,
                previous_slide_url=prev_slide_url,
                slot_idx=i,
                aspect_ratio=aspect_ratio,
                model_name_override=model_name_override,
            )

            if slide_url:
                slots[i]["url"] = slide_url
                slots[i]["status"] = "done"
                prev_slide_url = slide_url
                done += 1
            else:
                slots[i]["status"] = "failed"

            timeline_bytes = json.dumps(images_timeline, ensure_ascii=False).encode("utf-8")
            await self.storage_service.upload_timeline_file(
                file_data=timeline_bytes,
                object_name=object_key,
                content_type="application/json",
            )

        return {
            "lecture_id": lecture_id,
            "images_timeline_url": images_timeline_url,
            "total": total,
            "done": done,
        }
