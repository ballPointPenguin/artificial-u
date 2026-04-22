from __future__ import annotations

import html
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from artificial_u.api.config import Settings, get_settings
from artificial_u.api.dependencies import get_repository_factory
from artificial_u.models.repositories import RepositoryFactory

router = APIRouter(tags=["Share"])


def _public_web_base_url(request: Request, settings: Settings) -> str:
    base = (settings.PUBLIC_WEB_URL or "").strip()
    if base:
        return base.rstrip("/")
    return str(request.base_url).rstrip("/")


def _default_og_image_url(base: str, settings: Settings) -> str:
    if settings.PUBLIC_OG_DEFAULT_IMAGE_URL:
        return settings.PUBLIC_OG_DEFAULT_IMAGE_URL
    return f"{base}/icons/icon-512x512.png"


def _share_html(
    *,
    title: str,
    description: str,
    canonical_url: str,
    image_url: str,
    redirect_to: str,
) -> str:
    t = html.escape(title)
    d = html.escape(description)
    u = html.escape(canonical_url)
    img = html.escape(image_url)
    dest = html.escape(redirect_to)

    # Notes:
    # - Link unfurlers (Slack/iMessage/Discord/etc) fetch HTML and read <meta> tags.
    # - They do not execute JS, so the OG/Twitter tags must be present in the HTML response.
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{t}</title>

    <link rel="canonical" href="{u}" />

    <meta property="og:type" content="article" />
    <meta property="og:title" content="{t}" />
    <meta property="og:description" content="{d}" />
    <meta property="og:url" content="{u}" />
    <meta property="og:image" content="{img}" />

    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{t}" />
    <meta name="twitter:description" content="{d}" />
    <meta name="twitter:image" content="{img}" />

    <meta http-equiv="refresh" content="0; url={dest}" />
  </head>
  <body>
    <p>
      Redirecting to <a href="{dest}">the content</a>…
    </p>
  </body>
</html>
"""


def _truncate_description(text: Optional[str], *, fallback: str, max_len: int = 240) -> str:
    raw = (text or "").strip()
    if not raw:
        return fallback
    if len(raw) <= max_len:
        return raw
    return f"{raw[: max_len - 1].rstrip()}…"


@router.get("/share/courses/{course_id}", response_class=HTMLResponse)
def share_course(
    request: Request,
    course_id: int,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    settings: Settings = Depends(get_settings),
):
    base = _public_web_base_url(request, settings)

    course = repository_factory.course.get(course_id)
    if not course:
        url = f"{base}/courses/{course_id}"
        return HTMLResponse(
            _share_html(
                title="Course not found",
                description="This course may have been removed.",
                canonical_url=url,
                image_url=_default_og_image_url(base, settings),
                redirect_to=url,
            ),
            status_code=404,
            headers={"Cache-Control": "no-store"},
        )

    web_url = f"{base}/courses/{course_id}"
    share_url = f"{base}/share/courses/{course_id}"
    title = f"{course.code}: {course.title}"
    description = _truncate_description(
        course.description,
        fallback="Explore this course on ArtificialU.",
    )
    image_url = course.image_url or _default_og_image_url(base, settings)

    return HTMLResponse(
        _share_html(
            title=title,
            description=description,
            canonical_url=web_url,
            image_url=image_url,
            redirect_to=web_url,
        ),
        headers={
            "Cache-Control": "public, max-age=300",
            "X-Share-Url": share_url,
        },
    )


@router.get("/share/courses/{course_id}/topics/{topic_id}", response_class=HTMLResponse)
def share_topic(
    request: Request,
    course_id: int,
    topic_id: int,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    settings: Settings = Depends(get_settings),
):
    base = _public_web_base_url(request, settings)

    course = repository_factory.course.get(course_id)
    topic = repository_factory.topic.get(topic_id)
    if not course or not topic or topic.course_id != course_id:
        url = f"{base}/courses/{course_id}/topics/{topic_id}"
        return HTMLResponse(
            _share_html(
                title="Topic not found",
                description="This topic may have been removed.",
                canonical_url=url,
                image_url=_default_og_image_url(base, settings),
                redirect_to=url,
            ),
            status_code=404,
            headers={"Cache-Control": "no-store"},
        )

    web_url = f"{base}/courses/{course_id}/topics/{topic_id}"
    title = f"{course.code} · Week {topic.week}" + (
        f" Topic {topic.order}" if topic.order > 1 else ""
    )
    title = f"{title}: {topic.title}"
    description = _truncate_description(
        str(topic.content) if topic.content is not None else None,
        fallback=f"{course.code}: {course.title}",
    )
    image_url = course.image_url or _default_og_image_url(base, settings)

    return HTMLResponse(
        _share_html(
            title=title,
            description=description,
            canonical_url=web_url,
            image_url=image_url,
            redirect_to=web_url,
        ),
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/share/courses/{course_id}/lectures/{lecture_id}", response_class=HTMLResponse)
def share_lecture(
    request: Request,
    course_id: int,
    lecture_id: int,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    settings: Settings = Depends(get_settings),
):
    base = _public_web_base_url(request, settings)

    course = repository_factory.course.get(course_id)
    lecture = repository_factory.lecture.get(lecture_id)
    if not course or not lecture or lecture.course_id != course_id:
        url = f"{base}/courses/{course_id}/lectures/{lecture_id}"
        return HTMLResponse(
            _share_html(
                title="Lecture not found",
                description="This lecture may have been removed.",
                canonical_url=url,
                image_url=_default_og_image_url(base, settings),
                redirect_to=url,
            ),
            status_code=404,
            headers={"Cache-Control": "no-store"},
        )

    topic = repository_factory.topic.get(lecture.topic_id) if lecture.topic_id else None

    web_url = f"{base}/courses/{course_id}/lectures/{lecture_id}"
    title_bits = [course.code, lecture.title]
    if topic:
        title_bits.insert(1, f"Week {topic.week}")
    title = " · ".join(title_bits)

    description = _truncate_description(
        lecture.summary,
        fallback=(topic.title if topic else f"{course.code}: {course.title}"),
    )
    image_url = course.image_url or _default_og_image_url(base, settings)

    return HTMLResponse(
        _share_html(
            title=title,
            description=description,
            canonical_url=web_url,
            image_url=image_url,
            redirect_to=web_url,
        ),
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/share/professors/{professor_id}", response_class=HTMLResponse)
def share_professor(
    request: Request,
    professor_id: int,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    settings: Settings = Depends(get_settings),
):
    base = _public_web_base_url(request, settings)

    professor = repository_factory.professor.get(professor_id)
    if not professor:
        url = f"{base}/professors/{professor_id}"
        return HTMLResponse(
            _share_html(
                title="Professor not found",
                description="This professor may have been removed.",
                canonical_url=url,
                image_url=_default_og_image_url(base, settings),
                redirect_to=url,
            ),
            status_code=404,
            headers={"Cache-Control": "no-store"},
        )

    web_url = f"{base}/professors/{professor_id}"
    title = professor.name if professor.title is None else f"{professor.name} · {professor.title}"
    description = _truncate_description(
        professor.specialization or professor.background or professor.description,
        fallback="Meet this professor on ArtificialU.",
    )
    image_url = professor.image_url or _default_og_image_url(base, settings)

    return HTMLResponse(
        _share_html(
            title=title,
            description=description,
            canonical_url=web_url,
            image_url=image_url,
            redirect_to=web_url,
        ),
        headers={"Cache-Control": "public, max-age=300"},
    )
