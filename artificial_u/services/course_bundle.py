"""
Shared constants and helpers for the course export/import archive format.

Archive layout (format 2.x)::

    manifest.json            export_version, exported_at, source course info, counts, warnings
    course.json              course record (+ tags, connected_course_codes, assets.image)
    professor.json           professor record (+ voice metadata, assets.image)   [optional]
    department.json          department record (+ faculty metadata)              [optional]
    topics.json              list of topic records
    lectures.json            list of lecture records (+ voice metadata, assets.*)
    assets/...               binary/text assets, referenced from records via ``assets``

Records are keyed by the *source* instance's ids. Those ids are only used inside
the archive (to link lectures to topics and to name asset files); an importer
must never assume they are valid ids on the destination instance.

Compatibility rules:
- Exports are versioned ``MAJOR.MINOR``. New optional fields bump MINOR; anything an
  importer can't ignore bumps MAJOR.
- Importers accept any MAJOR <= ``FORMAT_MAJOR`` and ignore unknown fields. Missing
  fields fall back to defaults, so older archives keep importing as the model grows.
"""

import posixpath
from typing import Optional
from urllib.parse import urlparse

FORMAT_VERSION = "2.0"
FORMAT_MAJOR = 2

MANIFEST_PATH = "manifest.json"
COURSE_PATH = "course.json"
PROFESSOR_PATH = "professor.json"
DEPARTMENT_PATH = "department.json"
TOPICS_PATH = "topics.json"
LECTURES_PATH = "lectures.json"


def asset_ext(url_or_path: Optional[str], default: str) -> str:
    """Return a lowercase file extension (no dot) for a storage URL or key."""
    if not url_or_path:
        return default
    name = posixpath.basename(urlparse(url_or_path).path)
    if "." not in name:
        return default
    ext = name.rsplit(".", 1)[-1].lower()
    return ext if ext.isalnum() and len(ext) <= 5 else default


def course_image_path(ext: str) -> str:
    return f"assets/course/image.{ext}"


def professor_image_path(ext: str) -> str:
    return f"assets/professor/image.{ext}"


def audio_path(lecture_id: int, ext: str = "mp3") -> str:
    return f"assets/audio/lecture_{lecture_id}.{ext}"


def transcript_path(lecture_id: int, ext: str = "txt") -> str:
    return f"assets/transcripts/lecture_{lecture_id}.{ext}"


def timeline_path(lecture_id: int) -> str:
    return f"assets/timelines/lecture_{lecture_id}.json"


def images_timeline_path(lecture_id: int) -> str:
    return f"assets/lecture_images/lecture_{lecture_id}/timeline.json"


def lecture_image_path(lecture_id: int, slot_index: int, ext: str = "png") -> str:
    return f"assets/lecture_images/lecture_{lecture_id}/{slot_index:02d}.{ext}"


def parse_major(version: Optional[str]) -> Optional[int]:
    """Parse the MAJOR component of an export version string ("1.0" -> 1)."""
    try:
        return int(str(version).split(".", 1)[0])
    except TypeError, ValueError:
        return None
