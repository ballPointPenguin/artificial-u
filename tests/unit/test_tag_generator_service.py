from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.models.core import Course, Tag, Topic
from artificial_u.models.repositories.tag import TagRepository
from artificial_u.services.tag_generator_service import TagGeneratorService
from artificial_u.utils import ContentGenerationError


def _build_service(course=None, raw_response=None, top_names=None):
    course = course or Course(
        id=1,
        code="CS101",
        title="Introduction to AI",
        description="Foundations of AI",
        level="Undergraduate",
        department_id=3,
        language="en",
    )

    course_service = MagicMock()
    course_service.get_course.return_value = course

    content_service = MagicMock()
    content_service.generate_text = AsyncMock(
        return_value=raw_response
        or "<output><tags><tag>Machine Learning</tag><tag>Ethics</tag></tags></output>"
    )

    repository_factory = MagicMock()
    department = MagicMock()
    department.name = "Computer Science"
    repository_factory.department.get.return_value = department
    repository_factory.topic.list_by_course.return_value = [
        Topic(id=1, title="Search", course_id=1, week=1, order=1),
        Topic(id=2, title="Neural Networks", course_id=1, week=2, order=1),
    ]
    repository_factory.tag.list_top_names.return_value = top_names or ["Ethics"]

    def get_or_create(names, language="en"):
        return [
            Tag(id=i + 1, slug=TagRepository.slugify(name), name=name, language=language)
            for i, name in enumerate(names)
        ]

    repository_factory.tag.get_or_create_by_names.side_effect = get_or_create
    repository_factory.tag.set_course_tags.side_effect = lambda course_id, tag_ids: [
        Tag(id=tag_id, slug=f"tag-{tag_id}", name=f"Tag {tag_id}", language=course.language or "en")
        for tag_id in tag_ids
    ]

    service = TagGeneratorService(
        course_service=course_service,
        content_service=content_service,
        repository_factory=repository_factory,
        logger=MagicMock(),
    )
    return service, repository_factory, content_service


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generates_and_saves_tags_in_course_language():
    service, repos, content = _build_service()

    saved = await service.generate_tags_for_course(1)

    repos.tag.list_top_names.assert_called_once_with(language="en", limit=100)
    repos.tag.get_or_create_by_names.assert_called_once_with(
        ["Machine Learning", "Ethics"], language="en"
    )
    repos.tag.set_course_tags.assert_called_once_with(1, [1, 2])
    assert len(saved) == 2

    # Prompt carries course context and vocabulary
    prompt = content.generate_text.call_args.kwargs["prompt"]
    assert "CS101" in prompt
    assert "Ethics" in prompt


@pytest.mark.unit
@pytest.mark.asyncio
async def test_french_course_uses_french_universe():
    course = Course(
        id=2,
        code="PHI205",
        title="Philosophie de l'esprit",
        description="Un cours.",
        language="fr",
    )
    service, repos, _ = _build_service(
        course=course,
        raw_response="<output><tags><tag>Philosophie</tag></tags></output>",
    )

    await service.generate_tags_for_course(2)

    repos.tag.list_top_names.assert_called_once_with(language="fr", limit=100)
    repos.tag.get_or_create_by_names.assert_called_once_with(["Philosophie"], language="fr")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_bare_tags_block_without_output_wrapper_is_accepted():
    service, repos, _ = _build_service(
        raw_response="<tags><tag>Logic</tag><tag>Rhetoric</tag></tags>"
    )

    await service.generate_tags_for_course(1)

    repos.tag.get_or_create_by_names.assert_called_once_with(["Logic", "Rhetoric"], language="en")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_unparseable_response_raises_content_generation_error():
    service, _, _ = _build_service(raw_response="I could not think of any tags, sorry!")

    with pytest.raises(ContentGenerationError):
        await service.generate_tags_for_course(1)
