"""
Course import service for ArtificialU.

Reads an archive produced by ``CourseExportService`` (any supported format version)
and recreates the course on this instance. Import is two-step so an admin can resolve
ambiguity first:

1. ``analyze``  - read-only; reports what the archive holds and what would collide
   with existing data (course code, professor, department, voices, connected courses).
2. ``execute``  - performs the import using the admin's ``resolutions``.

Source ids in the archive are never trusted as destination ids; every reference is
re-resolved by natural key (department code/name, professor name, voice id, course code).
"""

import io
import json
import logging
import uuid
import zipfile
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, Optional, Set, Tuple

from artificial_u.models.core import (
    Course,
    Department,
    Faculty,
    Lecture,
    Professor,
    Topic,
    Voice,
)
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services import course_bundle as bundle
from artificial_u.services.course_purge_service import CoursePurgeService, StorageKey
from artificial_u.services.storage_service import StorageService

# Guard against zip bombs / absurd uploads (uncompressed bytes).
MAX_UNCOMPRESSED_BYTES = 2 * 1024**3

CONTENT_TYPES = {
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "gif": "image/gif",
    "json": "application/json",
    "md": "text/markdown",
    "txt": "text/plain",
}

COURSE_CODE_ACTIONS = ("replace", "rename", "cancel")


class ImportArchiveError(ValueError):
    """The archive is unreadable, malformed, or from an unsupported format version."""


class ImportConflictError(ValueError):
    """The import needs an admin decision (or the decision given is invalid)."""


class ImportCancelled(Exception):
    """The admin chose to cancel the import."""


@dataclass
class ParsedBundle:
    """An archive normalized to the current in-memory shape (older formats upgraded)."""

    version: str
    manifest: Dict[str, Any]
    course: Dict[str, Any]
    professor: Optional[Dict[str, Any]]
    department: Optional[Dict[str, Any]]
    topics: List[Dict[str, Any]]
    lectures: List[Dict[str, Any]]
    zip_file: zipfile.ZipFile
    warnings: List[str] = field(default_factory=list)

    @cached_property
    def names(self) -> Set[str]:
        return set(self.zip_file.namelist())

    def has(self, path: Optional[str]) -> bool:
        return bool(path) and path in self.names

    def read(self, path: str) -> bytes:
        return self.zip_file.read(path)


def _norm(value: Optional[str]) -> str:
    return " ".join((value or "").split()).casefold()


def _content_type(path: str, default: str = "application/octet-stream") -> str:
    return CONTENT_TYPES.get(bundle.asset_ext(path, ""), default)


class CourseImportService:
    """Service for importing a course archive into this instance."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        storage_service: StorageService,
        logger=None,
    ):
        self.repository_factory = repository_factory
        self.storage_service = storage_service
        self.logger = logger or logging.getLogger(__name__)
        self.purge_service = CoursePurgeService(repository_factory, storage_service, self.logger)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def parse_archive(self, data: bytes) -> ParsedBundle:  # noqa: C901
        """Open and normalize an archive. Raises ImportArchiveError if unusable."""
        try:
            zf = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile as e:
            raise ImportArchiveError("File is not a valid zip archive") from e

        if sum(i.file_size for i in zf.infolist()) > MAX_UNCOMPRESSED_BYTES:
            raise ImportArchiveError("Archive is too large to import")

        names = set(zf.namelist())

        def load(path: str, required: bool = False) -> Any:
            if path not in names:
                if required:
                    raise ImportArchiveError(f"Archive is missing {path}")
                return None
            try:
                return json.loads(zf.read(path).decode("utf-8"))
            except ValueError as e:
                raise ImportArchiveError(f"{path} is not valid JSON") from e

        manifest = load(bundle.MANIFEST_PATH, required=True)
        version = str(manifest.get("export_version", ""))
        major = bundle.parse_major(version)
        if major is None:
            raise ImportArchiveError("Archive manifest has no valid export_version")
        if major > bundle.FORMAT_MAJOR:
            raise ImportArchiveError(
                f"Archive format {version} is newer than this instance supports "
                f"(max {bundle.FORMAT_MAJOR}.x). Update this instance first."
            )

        course = load(bundle.COURSE_PATH, required=True)
        if not course.get("code") or not course.get("title"):
            raise ImportArchiveError("course.json must have a code and title")

        parsed = ParsedBundle(
            version=version,
            manifest=manifest,
            course=course,
            professor=load(bundle.PROFESSOR_PATH),
            department=load(bundle.DEPARTMENT_PATH),
            topics=load(bundle.TOPICS_PATH) or [],
            lectures=load(bundle.LECTURES_PATH) or [],
            zip_file=zf,
        )
        self._upgrade_legacy_assets(parsed)

        topic_ids = {t.get("id") for t in parsed.topics}
        for lecture in parsed.lectures:
            if lecture.get("topic_id") not in topic_ids:
                raise ImportArchiveError(
                    f"Lecture {lecture.get('id')} references unknown topic {lecture.get('topic_id')}"
                )
        return parsed

    def _upgrade_legacy_assets(self, parsed: ParsedBundle) -> None:
        """Fill ``assets`` for format 1.x archives, which used fixed paths and no map."""
        names = parsed.names

        if parsed.professor is not None and "assets" not in parsed.professor:
            parsed.professor["assets"] = {}
            for path in sorted(names):
                if path.startswith("assets/professor/image."):
                    parsed.professor["assets"]["image"] = path
                    break

        for lecture in parsed.lectures:
            if "assets" in lecture:
                continue
            lid = lecture.get("id")
            assets: Dict[str, str] = {}
            audio = bundle.audio_path(lid)
            if audio in names:
                assets["audio"] = audio
            transcript = bundle.transcript_path(lid)
            if transcript in names:
                assets["transcript"] = transcript
            lecture["assets"] = assets

        for lecture in parsed.lectures:
            for role, url_field in (("audio", "audio_url"), ("transcript", "transcript_url")):
                if lecture.get(url_field) and not parsed.has(lecture["assets"].get(role)):
                    parsed.warnings.append(
                        f"Lecture '{lecture.get('title')}' had {role} in the source "
                        "but the archive doesn't include the file"
                    )

    # ------------------------------------------------------------------
    # Analysis (read-only)
    # ------------------------------------------------------------------

    def analyze(self, data: bytes) -> Dict[str, Any]:
        """Describe an archive and the decisions needed to import it."""
        parsed = self.parse_archive(data)
        repos = self.repository_factory
        course = parsed.course

        assets_present = {
            "audio": sum(1 for lec in parsed.lectures if parsed.has(lec["assets"].get("audio"))),
            "transcripts": sum(
                1 for lec in parsed.lectures if parsed.has(lec["assets"].get("transcript"))
            ),
            "timelines": sum(
                1 for lec in parsed.lectures if parsed.has(lec["assets"].get("timeline"))
            ),
            "lecture_images": sum(
                1
                for n in parsed.names
                if n.startswith("assets/lecture_images/") and not n.endswith("/timeline.json")
            ),
            "course_image": int(parsed.has((course.get("assets") or {}).get("image"))),
            "professor_image": int(
                parsed.has(((parsed.professor or {}).get("assets") or {}).get("image"))
            ),
        }

        existing = repos.course.get_by_code(course["code"])
        code_conflict = None
        if existing:
            lecture_count = len(repos.lecture.list_by_course(existing.id))
            professor = (
                repos.professor.get(existing.professor_id) if existing.professor_id else None
            )
            code_conflict = {
                "existing": {
                    "id": existing.id,
                    "code": existing.code,
                    "title": existing.title,
                    "professor_name": professor.name if professor else None,
                    "lecture_count": lecture_count,
                    "status": existing.status,
                    "updated_at": existing.updated_at.isoformat() if existing.updated_at else None,
                },
                "same_title": _norm(existing.title) == _norm(course["title"]),
                "options": list(COURSE_CODE_ACTIONS),
                "suggested_code": self._suggest_code(course["code"]),
            }

        connected = course.get("connected_course_codes") or []
        found = [c for c in connected if repos.course.get_by_code(c)]

        return {
            "export_version": parsed.version,
            "exported_at": parsed.manifest.get("exported_at"),
            "course": {
                "code": course["code"],
                "title": course["title"],
                "language": course.get("language"),
                "status": course.get("status"),
                "topics": len(parsed.topics),
                "lectures": len(parsed.lectures),
            },
            "assets": assets_present,
            "tags": [t.get("name") for t in course.get("tags") or []],
            "course_code_conflict": code_conflict,
            "department": self._plan_department(parsed.department),
            "professor": self._plan_professor(parsed.professor),
            "voices": self._plan_voices(parsed),
            "connected_courses": {
                "found": found,
                "missing": [c for c in connected if c not in found],
            },
            "warnings": list(parsed.manifest.get("warnings") or []) + parsed.warnings,
        }

    def _suggest_code(self, code: str) -> str:
        n = 2
        while self.repository_factory.course.get_by_code(f"{code}-{n}"):
            n += 1
        return f"{code}-{n}"

    def _find_department(self, dept: Dict[str, Any]) -> Tuple[Optional[Department], Optional[str]]:
        repos = self.repository_factory
        if dept.get("code"):
            match = repos.department.get_by_code(dept["code"])
            if match:
                return match, "code"
        for candidate in repos.department.list():
            if _norm(candidate.name) == _norm(dept.get("name")):
                return candidate, "name"
        return None, None

    def _plan_department(self, dept: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not dept:
            return {"action": "none"}
        match, match_by = self._find_department(dept)
        return {
            "action": "match" if match else "create",
            "name": dept.get("name"),
            "code": dept.get("code"),
            "match": (
                {"id": match.id, "name": match.name, "code": match.code, "matched_by": match_by}
                if match
                else None
            ),
        }

    def _professor_candidates(self, prof: Dict[str, Any]) -> List[Professor]:
        name = _norm(prof.get("name"))
        return [p for p in self.repository_factory.professor.list() if _norm(p.name) == name]

    def _plan_professor(self, prof: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not prof:
            return {"action": "none"}
        candidates = self._professor_candidates(prof)
        repos = self.repository_factory
        out = []
        for p in candidates:
            department = repos.department.get(p.department_id) if p.department_id else None
            out.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "title": p.title,
                    "specialization": p.specialization,
                    "department": department.name if department else None,
                }
            )
        return {
            "action": "reuse" if candidates else "create",
            "name": prof.get("name"),
            "title": prof.get("title"),
            "specialization": prof.get("specialization"),
            "candidates": out,
        }

    def _find_voice(self, voice: Dict[str, Any]) -> Optional[Voice]:
        repos = self.repository_factory
        if voice.get("el_voice_id"):
            match = repos.voice.get_by_elevenlabs_id(voice["el_voice_id"])
            if match:
                return match
        if voice.get("external_id"):
            return repos.voice.get_by_external_id(
                voice.get("tts_backend") or "elevenlabs", voice["external_id"]
            )
        return None

    def _bundle_voices(self, parsed: ParsedBundle) -> List[Dict[str, Any]]:
        seen: Set[Tuple[Any, ...]] = set()
        voices = []
        for record in [parsed.professor or {}, *parsed.lectures]:
            voice = record.get("voice")
            if not voice:
                continue
            key = (voice.get("tts_backend"), voice.get("el_voice_id"), voice.get("external_id"))
            if key not in seen:
                seen.add(key)
                voices.append(voice)
        return voices

    def _plan_voices(self, parsed: ParsedBundle) -> List[Dict[str, Any]]:
        plan = []
        for voice in self._bundle_voices(parsed):
            match = self._find_voice(voice)
            can_create = bool(voice.get("el_voice_id") or voice.get("external_id"))
            plan.append(
                {
                    "name": voice.get("name"),
                    "tts_backend": voice.get("tts_backend") or "elevenlabs",
                    "action": "match" if match else ("create" if can_create else "skip"),
                }
            )
        return plan

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute(
        self,
        data: bytes,
        resolutions: Optional[Dict[str, Any]] = None,
        student_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Import the archive.

        Resolutions (all optional unless a conflict exists):
            course_code: "replace" | "rename" | "cancel" - required if the code exists
            new_code: str - the code to use when course_code == "rename"
            professor: "reuse" | "create" - default "reuse" if a same-named professor exists
            professor_id: int - which existing professor to reuse (default: first match)
            hidden: bool - import as hidden regardless of the exported status

        Raises:
            ImportArchiveError, ImportConflictError, ImportCancelled
        """
        resolutions = resolutions or {}
        parsed = self.parse_archive(data)
        repos = self.repository_factory
        source = parsed.course

        final_code, replace_id = self._resolve_course_code(source["code"], resolutions)

        ctx = _ImportContext(
            code=final_code, student_id=student_id, written=set(), warnings=list(parsed.warnings)
        )
        # Replacing: build the new course under a temporary code, swap in at the end,
        # so a failed import never costs the admin the course they already have.
        working_code = f"{final_code}__import_{uuid.uuid4().hex[:8]}" if replace_id else final_code

        try:
            department = await self._import_department(parsed.department, ctx)
            professor = await self._import_professor(parsed, department, resolutions, ctx)

            course = Course(
                code=working_code,
                title=source["title"],
                description=source.get("description"),
                lectures_per_week=source.get("lectures_per_week") or 1,
                level=source.get("level"),
                total_weeks=source.get("total_weeks") or 12,
                language=source.get("language"),
                status="hidden" if resolutions.get("hidden") else source.get("status") or "hidden",
                notes=source.get("notes"),
                department_id=(department.id if department else None),
                professor_id=professor.id if professor else None,
                created_by=student_id,
                created_with=source.get("created_with"),
                image_created_with=source.get("image_created_with"),
            )
            course = repos.course.create(course)
            ctx.course_id = course.id

            image_path = (source.get("assets") or {}).get("image")
            if parsed.has(image_path):
                url = await self._upload_unique_image(parsed.read(image_path), image_path, ctx)
                if url:
                    course.image_url = url
                    repos.course.update(course)

            topic_map = self._import_topics(parsed, course.id, ctx)
            lecture_count = await self._import_lectures(parsed, course, topic_map, ctx)
            self._import_tags(source, course.id)

            old_connections: List[int] = []
            if replace_id:
                old = repos.course.get(replace_id)
                old_connections = [c for c in (old.connected_course_ids if old else [])]
                await self.purge_service.purge_course(replace_id, keep_keys=ctx.written)
                course.code = final_code
                repos.course.update(course)

            connections = self._connection_ids(source, course.id, final_code, old_connections)
            if connections:
                repos.course.set_connected_courses(course.id, connections)
        except Exception:
            await self._rollback(ctx)
            raise

        return {
            "course_id": course.id,
            "course_code": final_code,
            "course_title": course.title,
            "replaced_course_id": replace_id,
            "professor_id": professor.id if professor else None,
            "department_id": department.id if department else None,
            "topics_created": len(topic_map),
            "lectures_created": lecture_count,
            "assets_uploaded": len(ctx.written),
            "warnings": ctx.warnings,
        }

    def _resolve_course_code(
        self, source_code: str, resolutions: Dict[str, Any]
    ) -> Tuple[str, Optional[int]]:
        """Return (final_code, id_of_course_to_replace)."""
        existing = self.repository_factory.course.get_by_code(source_code)
        action = resolutions.get("course_code")

        if not existing:
            if action == "cancel":
                raise ImportCancelled()
            return source_code, None

        if action is None:
            raise ImportConflictError(
                f"Course code {source_code} already exists; choose replace, rename, or cancel"
            )
        if action == "cancel":
            raise ImportCancelled()
        if action == "replace":
            return source_code, existing.id
        if action == "rename":
            new_code = (resolutions.get("new_code") or "").strip()
            if not new_code:
                raise ImportConflictError("new_code is required to rename")
            if self.repository_factory.course.get_by_code(new_code):
                raise ImportConflictError(f"Course code {new_code} already exists")
            return new_code, None
        raise ImportConflictError(f"Unknown course_code resolution: {action}")

    async def _import_department(
        self, dept: Optional[Dict[str, Any]], ctx: "_ImportContext"
    ) -> Optional[Department]:
        if not dept:
            return None
        repos = self.repository_factory
        match, _ = self._find_department(dept)
        if match:
            return match

        faculty_id = None
        faculty = dept.get("faculty") or (
            {"name": dept["faculty_name"]} if dept.get("faculty_name") else None
        )
        if faculty and faculty.get("name"):
            existing = repos.faculty.get_by_name(faculty["name"])
            if not existing:
                existing = repos.faculty.create(
                    Faculty(
                        name=faculty["name"],
                        description=faculty.get("description"),
                        language=faculty.get("language"),
                    )
                )
                ctx.created_faculty_id = existing.id
            faculty_id = existing.id

        created = repos.department.create(
            Department(
                name=dept["name"],
                code=dept["code"],
                faculty_id=faculty_id,
                description=dept.get("description"),
                language=dept.get("language"),
            )
        )
        ctx.created_department_id = created.id
        return created

    async def _import_professor(
        self,
        parsed: ParsedBundle,
        department: Optional[Department],
        resolutions: Dict[str, Any],
        ctx: "_ImportContext",
    ) -> Optional[Professor]:
        prof = parsed.professor
        if not prof:
            return None
        repos = self.repository_factory

        candidates = self._professor_candidates(prof)
        action = resolutions.get("professor") or ("reuse" if candidates else "create")
        if action == "reuse":
            wanted = resolutions.get("professor_id")
            for candidate in candidates:
                if wanted is None or candidate.id == wanted:
                    return candidate
            raise ImportConflictError("No matching existing professor to reuse")
        if action != "create":
            raise ImportConflictError(f"Unknown professor resolution: {action}")

        voice = await self._import_voice(prof.get("voice"), ctx)
        professor = Professor(
            name=prof["name"],
            title=prof.get("title"),
            accent=prof.get("accent"),
            age=prof.get("age"),
            background=prof.get("background"),
            description=prof.get("description"),
            gender=prof.get("gender"),
            personality=prof.get("personality"),
            specialization=prof.get("specialization"),
            teaching_style=prof.get("teaching_style"),
            language=prof.get("language"),
            tts_backend=prof.get("tts_backend"),
            image_created_with=prof.get("image_created_with"),
            department_id=department.id if department else None,
            voice_id=voice.id if voice else None,
            created_by=ctx.student_id,
            created_with=prof.get("created_with"),
        )
        professor = repos.professor.create(professor)
        ctx.created_professor_id = professor.id

        image_path = (prof.get("assets") or {}).get("image")
        if parsed.has(image_path):
            url = await self._upload_unique_image(parsed.read(image_path), image_path, ctx)
            if url:
                professor.image_url = url
                repos.professor.update(professor)
        return professor

    async def _import_voice(
        self, voice: Optional[Dict[str, Any]], ctx: "_ImportContext"
    ) -> Optional[Voice]:
        """Match a voice by its provider id, else recreate it from archived metadata."""
        if not voice:
            return None
        cache_key = (voice.get("tts_backend"), voice.get("el_voice_id"), voice.get("external_id"))
        if cache_key in ctx.voices:
            return ctx.voices[cache_key]

        match = self._find_voice(voice)
        if not match and (voice.get("el_voice_id") or voice.get("external_id")):
            match = self.repository_factory.voice.create(
                Voice(
                    tts_backend=voice.get("tts_backend") or "elevenlabs",
                    external_id=voice.get("external_id"),
                    el_voice_id=voice.get("el_voice_id"),
                    name=voice.get("name"),
                    accent=voice.get("accent"),
                    age=voice.get("age"),
                    category=voice.get("category"),
                    description=voice.get("description"),
                    descriptive=voice.get("descriptive"),
                    gender=voice.get("gender"),
                    language=voice.get("language"),
                    locale=voice.get("locale"),
                    use_case=voice.get("use_case"),
                )
            )
        elif not match:
            ctx.warnings.append(f"Voice '{voice.get('name')}' has no provider id; left unset")
        ctx.voices[cache_key] = match
        return match

    def _import_topics(
        self, parsed: ParsedBundle, course_id: int, ctx: "_ImportContext"
    ) -> Dict[Any, Topic]:
        topics: Dict[Any, Topic] = {}
        for t in sorted(parsed.topics, key=lambda x: (x.get("week", 1), x.get("order", 1))):
            topics[t["id"]] = self.repository_factory.topic.create(
                Topic(
                    title=t["title"],
                    order=t.get("order") or 1,
                    week=t.get("week") or 1,
                    content=t.get("content"),
                    language=t.get("language"),
                    course_id=course_id,
                    created_by=ctx.student_id,
                    created_with=t.get("created_with"),
                )
            )
        return topics

    async def _import_lectures(  # noqa: C901
        self,
        parsed: ParsedBundle,
        course: Course,
        topics: Dict[Any, Topic],
        ctx: "_ImportContext",
    ) -> int:
        repos = self.repository_factory
        storage = self.storage_service
        used_keys: Set[StorageKey] = set()

        def unique(bucket: str, key: str, revision: Optional[int]) -> str:
            """Keep keys readable, but never let two revisions of a topic share one."""
            if (bucket, key) in used_keys and revision is not None:
                stem, dot, ext = key.rpartition(".")
                key = f"{stem}_r{revision}{dot}{ext}"
            used_keys.add((bucket, key))
            return key

        async def put(
            bucket: str, key: str, path: str, data: Optional[bytes] = None
        ) -> Optional[str]:
            ok, url = await storage.upload_file(
                data if data is not None else parsed.read(path),
                bucket,
                key,
                content_type=_content_type(path),
            )
            if not ok:
                raise RuntimeError(f"Failed to upload {path} to {bucket}/{key}")
            ctx.written.add((bucket, key))
            return url

        for src in sorted(parsed.lectures, key=lambda x: x.get("revision") or 0):
            topic = topics[src["topic_id"]]
            lecture = repos.lecture.create(
                Lecture(
                    revision=src.get("revision"),
                    content=src.get("content"),
                    summary=src.get("summary"),
                    title=src.get("title") or topic.title,
                    language=src.get("language"),
                    duration=src.get("duration"),
                    course_id=course.id,
                    topic_id=topic.id,
                    created_by=ctx.student_id,
                    created_with=src.get("created_with"),
                )
            )
            week, order, rev = topic.week, topic.order, lecture.revision
            assets = src.get("assets") or {}
            updates: Dict[str, Any] = {}

            voice = await self._import_voice(src.get("voice"), ctx)
            if voice:
                updates["voice_id"] = voice.id

            if parsed.has(assets.get("audio")):
                path = assets["audio"]
                ext = bundle.asset_ext(path, "mp3")
                key = unique(
                    storage.audio_bucket,
                    storage.generate_audio_key(ctx.code, week, order, ext),
                    rev,
                )
                updates["audio_url"] = await put(storage.audio_bucket, key, path)

            if parsed.has(assets.get("transcript")):
                path = assets["transcript"]
                ext = bundle.asset_ext(path, "txt")
                key = unique(
                    storage.lectures_bucket,
                    storage.generate_lecture_key(ctx.code, week, order, ext),
                    rev,
                )
                updates["transcript_url"] = await put(storage.lectures_bucket, key, path)

            if parsed.has(assets.get("timeline")):
                key = unique(
                    storage.lectures_bucket,
                    storage.generate_timeline_key(ctx.code, week, order),
                    rev,
                )
                updates["timeline_url"] = await put(
                    storage.lectures_bucket, key, assets["timeline"]
                )

            if parsed.has(assets.get("images_timeline")):
                images_url = await self._import_images_timeline(
                    parsed, assets["images_timeline"], ctx, week, order, rev, unique, put
                )
                if images_url:
                    updates["images_timeline_url"] = images_url

            if updates:
                repos.lecture.update_fields(lecture.id, updates)
        return len(parsed.lectures)

    async def _import_images_timeline(
        self, parsed, path, ctx, week, order, revision, unique, put
    ) -> Optional[str]:
        """Upload slide images and the timeline, rewriting slot urls to this instance."""
        storage = self.storage_service
        try:
            timeline = json.loads(parsed.read(path).decode("utf-8"))
        except ValueError:
            ctx.warnings.append(f"Images timeline {path} is not valid JSON; skipped")
            return None

        for fallback_idx, slot in enumerate(timeline.get("slots") or []):
            image_path = slot.get("url")
            if image_path and parsed.has(image_path):
                idx = int(slot.get("index", fallback_idx))
                key = storage.generate_lecture_image_key(
                    ctx.code, week, order, idx, bundle.asset_ext(image_path, "png")
                )
                slot["url"] = await put(storage.images_bucket, key, image_path)
            else:
                # Missing or foreign url: don't point at another instance's storage
                slot["url"] = None
                if slot.get("status") == "done":
                    slot["status"] = "pending"

        key = unique(
            storage.lectures_bucket,
            storage.generate_lecture_images_timeline_key(ctx.code, week, order),
            revision,
        )
        payload = json.dumps(timeline, ensure_ascii=False).encode("utf-8")
        return await put(storage.lectures_bucket, key, "images_timeline.json", payload)

    async def _upload_unique_image(
        self, data: bytes, path: str, ctx: "_ImportContext"
    ) -> Optional[str]:
        """Course/professor images use flat uuid keys in the images bucket."""
        ext = bundle.asset_ext(path, "png")
        bucket = self.storage_service.images_bucket
        key = f"{uuid.uuid4()}.{ext}"
        ok, url = await self.storage_service.upload_file(
            data, bucket, key, content_type=_content_type(path)
        )
        if not ok:
            ctx.warnings.append(f"Failed to upload {path}")
            return None
        ctx.written.add((bucket, key))
        return url

    def _import_tags(self, source: Dict[str, Any], course_id: int) -> None:
        repos = self.repository_factory
        by_language: Dict[str, List[str]] = {}
        for tag in source.get("tags") or []:
            language = tag.get("language") or source.get("language") or "en"
            by_language.setdefault(language, []).append(tag["name"])
        tag_ids = []
        for language, names in by_language.items():
            tag_ids += [t.id for t in repos.tag.get_or_create_by_names(names, language)]
        if tag_ids:
            repos.tag.set_course_tags(course_id, tag_ids)

    def _connection_ids(
        self, source: Dict[str, Any], course_id: int, final_code: str, carried: List[int]
    ) -> List[int]:
        ids = {c for c in carried if c != course_id}
        for code in source.get("connected_course_codes") or []:
            other = self.repository_factory.course.get_by_code(code)
            if other and other.id != course_id and code != final_code:
                ids.add(other.id)
        return sorted(ids)

    async def _rollback(self, ctx: "_ImportContext") -> None:
        """Undo a failed import: remove the partial course and anything we created."""
        repos = self.repository_factory
        self.logger.exception("Course import failed; rolling back")
        try:
            if ctx.course_id:
                await self.purge_service.purge_course(ctx.course_id)
            for bucket, key in ctx.written:
                await self.storage_service.delete_file(bucket, key)
            if ctx.created_professor_id:
                repos.professor.delete(ctx.created_professor_id)
            if ctx.created_department_id:
                repos.department.delete(ctx.created_department_id)
            if ctx.created_faculty_id:
                repos.faculty.delete(ctx.created_faculty_id)
        except Exception:
            self.logger.exception("Rollback of failed course import was incomplete")


@dataclass
class _ImportContext:
    code: str
    student_id: Optional[int]
    written: Set[StorageKey]
    warnings: List[str]
    course_id: Optional[int] = None
    created_professor_id: Optional[int] = None
    created_department_id: Optional[int] = None
    created_faculty_id: Optional[int] = None
    voices: Dict[Tuple[Any, ...], Optional[Voice]] = field(default_factory=dict)
