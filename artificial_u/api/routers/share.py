from __future__ import annotations

import html
import io
from typing import Optional
from urllib.parse import quote, urlparse

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response
from PIL import Image

from artificial_u.api.config import Settings, get_settings
from artificial_u.api.dependencies import get_http_client, get_repository_factory
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services.storage_service import StorageService

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


def _og_card_proxy_url(base: str, src_image_url: str) -> str:
    # Keep the original (square) image URL in storage, but serve a derived
    # 1200x630 top-cropped JPEG for social previews.
    return f"{base}/share/og-image?src={quote(src_image_url, safe='')}"


def _top_crop_to_aspect(img: Image.Image, *, aspect_w: int, aspect_h: int) -> Image.Image:
    """
    Crop to target aspect ratio, preferring the *top* when cropping height.
    """
    w, h = img.size
    target_ratio = aspect_w / aspect_h
    current_ratio = w / h if h else target_ratio

    if abs(current_ratio - target_ratio) < 1e-6:
        return img

    if current_ratio > target_ratio:
        # Too wide -> crop width (center horizontally)
        new_w = int(h * target_ratio)
        left = max(0, (w - new_w) // 2)
        return img.crop((left, 0, left + new_w, h))

    # Too tall -> crop height (TOP crop)
    new_h = int(w / target_ratio)
    new_h = min(new_h, h)
    return img.crop((0, 0, w, new_h))


@router.get("/share/og-image")
async def share_og_image(
    src: str = "",
    http_client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Generate a social-preview-friendly OG image from a stored square image:
    - Crops to 1200x630 aspect, preferring the top when losing height
    - Encodes as JPEG to reduce size (WhatsApp-friendly)
    """
    settings = get_settings()
    base = (settings.PUBLIC_WEB_URL or "").strip().rstrip("/")
    fallback_src = _default_og_image_url(base, settings)
    src = (src or "").strip() or fallback_src

    storage = StorageService()
    bucket, key = storage.parse_storage_url(src)
    data: bytes | None = None

    if bucket and key:
        data, _content_type = await storage.download_file(bucket, key)
    else:
        # Fallback: allow HTTP(S) URLs (e.g. app-served icons or CDN assets)
        parsed = urlparse(src)
        if parsed.scheme in {"http", "https"}:
            try:
                resp = await http_client.get(src, timeout=10.0)
                resp.raise_for_status()
                data = resp.content
            except Exception:
                data = None

    if not data and src != fallback_src:
        # Last-chance fallback to the default image
        bucket, key = storage.parse_storage_url(fallback_src)
        if bucket and key:
            data, _content_type = await storage.download_file(bucket, key)
        else:
            parsed = urlparse(fallback_src)
            if parsed.scheme in {"http", "https"}:
                try:
                    resp = await http_client.get(fallback_src, timeout=10.0)
                    resp.raise_for_status()
                    data = resp.content
                except Exception:
                    data = None

    if not data:
        return Response(status_code=404)

    try:
        with Image.open(io.BytesIO(data)) as im:
            im = im.convert("RGB")
            im = _top_crop_to_aspect(im, aspect_w=1200, aspect_h=630)
            im = im.resize((1200, 630), Image.Resampling.LANCZOS)

            out = io.BytesIO()
            im.save(out, format="JPEG", quality=75, optimize=True, progressive=True)
            out.seek(0)
            return Response(
                content=out.read(),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception:
        return Response(status_code=500)


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
    site_name = "ArtificialU"

    # Notes:
    # - Link unfurlers (Slack/iMessage/Discord/etc) fetch HTML and read <meta> tags.
    # - They do not execute JS, so the OG/Twitter tags must be present in the HTML response.
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{t}</title>

    <meta name="description" content="{d}" />
    <link rel="canonical" href="{u}" />

    <meta property="og:type" content="article" />
    <meta property="og:site_name" content="{site_name}" />
    <meta property="og:locale" content="en_US" />
    <meta property="og:title" content="{t}" />
    <meta property="og:description" content="{d}" />
    <meta property="og:url" content="{u}" />
    <meta property="og:image" content="{img}" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content="{t}" />

    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{t}" />
    <meta name="twitter:description" content="{d}" />
    <meta name="twitter:image" content="{img}" />
    <meta name="twitter:image:alt" content="{t}" />

    <meta http-equiv="refresh" content="0; url={dest}" />
  </head>
  <body>
    <p>
      Redirecting to <a href="{dest}">the content</a>…
    </p>
  </body>
</html>
"""


def _truncate_description(text: Optional[str], *, fallback: str, max_len: int = 160) -> str:
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
    og_image_url = _og_card_proxy_url(base, image_url)

    return HTMLResponse(
        _share_html(
            title=title,
            description=description,
            canonical_url=share_url,
            image_url=og_image_url,
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
    share_url = f"{base}/share/courses/{course_id}/topics/{topic_id}"
    title = f"{course.code} · Week {topic.week}" + (
        f" Topic {topic.order}" if topic.order > 1 else ""
    )
    title = f"{title}: {topic.title}"
    # Topic content is a JSON blob; for sharing use the lecture summary instead.
    lecture = (repository_factory.lecture.list_by_topic(topic_id) or [None])[0]
    description = _truncate_description(
        lecture.summary if lecture else None,
        fallback=topic.title or f"{course.code}: {course.title}",
    )
    image_url = course.image_url or _default_og_image_url(base, settings)
    og_image_url = _og_card_proxy_url(base, image_url)

    return HTMLResponse(
        _share_html(
            title=title,
            description=description,
            canonical_url=share_url,
            image_url=og_image_url,
            redirect_to=web_url,
        ),
        headers={"Cache-Control": "public, max-age=300", "X-Share-Url": share_url},
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
    share_url = f"{base}/share/courses/{course_id}/lectures/{lecture_id}"
    title_bits = [course.code, lecture.title]
    if topic:
        title_bits.insert(1, f"Week {topic.week}")
    title = " · ".join(title_bits)

    description = _truncate_description(
        lecture.summary,
        fallback=(topic.title if topic else f"{course.code}: {course.title}"),
    )
    image_url = course.image_url or _default_og_image_url(base, settings)
    og_image_url = _og_card_proxy_url(base, image_url)

    return HTMLResponse(
        _share_html(
            title=title,
            description=description,
            canonical_url=share_url,
            image_url=og_image_url,
            redirect_to=web_url,
        ),
        headers={"Cache-Control": "public, max-age=300", "X-Share-Url": share_url},
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
    share_url = f"{base}/share/professors/{professor_id}"
    title = professor.name if professor.title is None else f"{professor.name} · {professor.title}"
    description = _truncate_description(
        professor.specialization or professor.background or professor.description,
        fallback="Meet this professor on ArtificialU.",
    )
    image_url = professor.image_url or _default_og_image_url(base, settings)
    og_image_url = _og_card_proxy_url(base, image_url)

    return HTMLResponse(
        _share_html(
            title=title,
            description=description,
            canonical_url=share_url,
            image_url=og_image_url,
            redirect_to=web_url,
        ),
        headers={"Cache-Control": "public, max-age=300", "X-Share-Url": share_url},
    )
