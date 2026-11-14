"""Tests for the source restrictions of the OG image proxy."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.api.routers.share import _load_og_source

SETTINGS = SimpleNamespace(
    PUBLIC_WEB_URL="https://artificial-u.com",
    PUBLIC_OG_DEFAULT_IMAGE_URL=None,
)


def _storage(parsed):
    storage = MagicMock()
    storage.images_bucket = "au-images"
    storage.parse_storage_url.return_value = parsed
    storage.download_file = AsyncMock(return_value=(b"image-bytes", "image/png"))
    return storage


def _http_client():
    client = MagicMock()
    response = MagicMock(content=b"icon-bytes")
    client.get = AsyncMock(return_value=response)
    return client


@pytest.mark.unit
@pytest.mark.asyncio
async def test_loads_objects_from_the_images_bucket():
    storage, client = _storage(("au-images", "professors/1.png")), _http_client()

    data = await _load_og_source(
        "https://storage/au-images/professors/1.png", storage, client, SETTINGS
    )

    assert data == b"image-bytes"
    storage.download_file.assert_awaited_once_with("au-images", "professors/1.png")
    client.get.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refuses_objects_from_other_buckets():
    storage, client = _storage(("au-exports", "course-7.zip")), _http_client()

    data = await _load_og_source(
        "https://storage/au-exports/course-7.zip", storage, client, SETTINGS
    )

    assert data is None
    storage.download_file.assert_not_called()
    client.get.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "src",
    [
        "http://169.254.169.254/latest/meta-data/",
        "https://example.com/picture.png",
        "https://artificial-u.com.example.com/icon.png",
        "file:///etc/passwd",
        "/icons/icon-512x512.png",
    ],
)
async def test_refuses_urls_outside_our_public_site(src):
    storage, client = _storage((None, None)), _http_client()

    assert await _load_og_source(src, storage, client, SETTINGS) is None
    client.get.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetches_the_default_icon_from_our_public_site():
    storage, client = _storage((None, None)), _http_client()
    src = "https://artificial-u.com/icons/icon-512x512.png"

    assert await _load_og_source(src, storage, client, SETTINGS) == b"icon-bytes"
    client.get.assert_awaited_once()
