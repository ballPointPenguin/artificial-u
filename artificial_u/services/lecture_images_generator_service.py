import asyncio
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

import httpx

from artificial_u.services.http_client import get_shared_async_client
from artificial_u.services.image_service import ImageService
from artificial_u.services.storage_service import StorageService


class LectureImagesGeneratorService:
    """
    Generate synced lecture slideshow images (admin-triggered).

    v1 intentionally keeps a simple text chunking strategy, then best-effort
    maps each chunk to the forced-alignment word timeline for slide timing.
    """

    _timeline_locks: Dict[str, asyncio.Lock] = {}
    _token_re = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")

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

    def _normalize_tokens(self, text: str) -> List[str]:
        return self._token_re.findall((text or "").lower())

    def _timeline_words(self, timeline: Dict[str, Any]) -> List[Dict[str, Any]]:
        words: List[Dict[str, Any]] = []
        for event in timeline.get("events") or []:
            token = " ".join(self._normalize_tokens(str(event.get("content") or "")))
            if not token:
                continue
            words.append(
                {
                    "token": token,
                    "start": float(event.get("start") or 0.0),
                    "end": float(event.get("end") or 0.0),
                }
            )
        return words

    def _sequence_matches_at(
        self, timeline_words: List[Dict[str, Any]], start_idx: int, sequence: List[str]
    ) -> bool:
        if start_idx + len(sequence) > len(timeline_words):
            return False
        return all(
            timeline_words[start_idx + offset]["token"] == token
            for offset, token in enumerate(sequence)
        )

    def _find_chunk_start(
        self,
        chunk_tokens: List[str],
        timeline_words: List[Dict[str, Any]],
        cursor: int,
        *,
        min_prefix_words: int = 5,
        max_prefix_words: int = 12,
    ) -> Optional[Dict[str, Any]]:
        if not chunk_tokens or not timeline_words:
            return None

        max_prefix = min(max_prefix_words, len(chunk_tokens))
        min_prefix = min(min_prefix_words, max_prefix)
        best_candidates: List[int] = []
        best_prefix_len = min_prefix

        for prefix_len in range(min_prefix, max_prefix + 1):
            sequence = chunk_tokens[:prefix_len]
            candidates = [
                idx
                for idx in range(cursor, len(timeline_words) - prefix_len + 1)
                if self._sequence_matches_at(timeline_words, idx, sequence)
            ]
            if len(candidates) == 1:
                return {"word_idx": candidates[0], "prefix_len": prefix_len}
            if candidates:
                best_candidates = candidates
                best_prefix_len = prefix_len

        if best_candidates:
            # The lecture is processed in order, so the first remaining match is usually correct.
            return {"word_idx": best_candidates[0], "prefix_len": best_prefix_len}

        return None

    def _even_slots(self, duration: float, total: int) -> List[Dict[str, float]]:
        return [
            {
                "start": (duration * i) / total,
                "end": (duration * (i + 1)) / total,
            }
            for i in range(total)
        ]

    def _timeline_informed_slots(  # noqa: C901
        self, chunks: List[str], timeline: Dict[str, Any], duration: float
    ) -> List[Dict[str, float]]:
        total = len(chunks)
        fallback_slots = self._even_slots(duration, total)
        timeline_words = self._timeline_words(timeline)
        if not timeline_words:
            return fallback_slots

        matched_starts: List[Optional[float]] = []
        cursor = 0
        for chunk in chunks:
            match = self._find_chunk_start(self._normalize_tokens(chunk), timeline_words, cursor)
            if not match:
                matched_starts.append(None)
                continue

            word_idx = int(match["word_idx"])
            matched_starts.append(float(timeline_words[word_idx]["start"]))
            cursor = word_idx + int(match["prefix_len"])

        matched_indices = [idx for idx, start in enumerate(matched_starts) if start is not None]
        if not matched_indices:
            return fallback_slots

        starts: List[float] = [0.0] * total
        for idx in matched_indices:
            starts[idx] = float(matched_starts[idx] or 0.0)

        first_matched_idx = matched_indices[0]
        first_matched_start = starts[first_matched_idx]
        for i in range(first_matched_idx):
            starts[i] = (first_matched_start * i) / max(1, first_matched_idx)

        for previous_idx, next_idx in zip(matched_indices, matched_indices[1:]):
            previous_start = starts[previous_idx]
            next_start = starts[next_idx]
            span = max(1, next_idx - previous_idx)
            for i in range(previous_idx + 1, next_idx):
                ratio = (i - previous_idx) / span
                starts[i] = previous_start + ((next_start - previous_start) * ratio)

        last_matched_idx = matched_indices[-1]
        last_matched_start = starts[last_matched_idx]
        trailing_span = max(1, total - last_matched_idx)
        for i in range(last_matched_idx + 1, total):
            ratio = (i - last_matched_idx) / trailing_span
            starts[i] = last_matched_start + ((duration - last_matched_start) * ratio)

        slots: List[Dict[str, float]] = []
        for i in range(total):
            start = starts[i]
            end = starts[i + 1] if i + 1 < total else duration
            if end <= start:
                end = fallback_slots[i]["end"]
            if end <= start:
                end = min(duration, start + 1.0)

            slots.append({"start": start, "end": end})

        return slots

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
        slot_times = self._timeline_informed_slots(chunks, timeline, duration)

        resolved_model_name = model_name_override or getattr(self.image_service, "model_name", None)
        batch_id = str(uuid.uuid4())

        # Build scaffold json and upload it first.
        slots: List[Dict[str, Any]] = []
        for i in range(total):
            start = slot_times[i]["start"]
            end = slot_times[i]["end"]
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
