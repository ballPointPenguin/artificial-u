from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.models.core import Course, Topic
from artificial_u.services.topic_generator_service import TopicGeneratorService


def _build_service(
    existing_topics=None,
    *,
    connected_course_ids=None,
    related_courses=None,
    topics_by_course_id=None,
):
    repository_factory = MagicMock()
    repository_factory.topic.get_by_course_week_order.return_value = None

    created_topics = []

    def create_topic(topic: Topic) -> Topic:
        created_topic = topic.model_copy(
            update={"id": len(created_topics) + 1, "created_at": "2026-03-20T00:00:00Z"}
        )
        created_topics.append(created_topic)
        return created_topic

    repository_factory.topic.create.side_effect = create_topic

    topic_service = MagicMock()
    topic_lookup = dict(topics_by_course_id or {})
    topic_lookup.setdefault(1, existing_topics or [])
    def list_topics_by_course(course_id: int):
        return topic_lookup.get(course_id, [])

    topic_service.list_topics_by_course.side_effect = list_topics_by_course

    course_service = MagicMock()
    main_course = Course(
        id=1,
        code="ATM200",
        title="Atmospheric Science",
        description="Study of the atmosphere",
        lectures_per_week=2,
        total_weeks=2,
        connected_course_ids=connected_course_ids or [],
    )
    course_lookup = {1: main_course}
    if related_courses:
        for course in related_courses:
            course_lookup[course.id] = course

    def get_course_by_id(course_id: int):
        return course_lookup[course_id]

    course_service.get_course.side_effect = get_course_by_id

    content_service = MagicMock()
    content_service.generate_text = AsyncMock()

    service = TopicGeneratorService(
        topic_service=topic_service,
        course_service=course_service,
        content_service=content_service,
        repository_factory=repository_factory,
        job_enqueue_service=MagicMock(),
        logger=MagicMock(),
    )

    return service, repository_factory, content_service, created_topics


@pytest.mark.asyncio
async def test_generate_topics_for_course_generates_missing_slots_sequentially(monkeypatch):
    monkeypatch.setattr(
        "artificial_u.services.topic_generator_service.get_settings",
        lambda: SimpleNamespace(TOPICS_GENERATION_MODEL="test-topics-model"),
    )

    service, repository_factory, content_service, created_topics = _build_service()
    content_service.generate_text.side_effect = [
        "<output><topic><title>Atmospheric Structure</title><week>1</week><order>1</order></topic></output>",
        "<output><topic><title>Trace Gases and Water Vapor</title><week>1</week><order>2</order></topic></output>",
        "<output><topic><title>Radiation and Energy Balance</title><week>2</week><order>1</order></topic></output>",
        (
            "<output><topic><title>Cloud Formation and Precipitation</title>"
            "<week>2</week><order>2</order></topic></output>"
        ),
    ]

    topics = await service.generate_topics_for_course(course_id=1, created_by=7)

    assert [(topic.week, topic.order) for topic in topics] == [(1, 1), (1, 2), (2, 1), (2, 2)]
    assert [topic.title for topic in topics] == [
        "Atmospheric Structure",
        "Trace Gases and Water Vapor",
        "Radiation and Energy Balance",
        "Cloud Formation and Precipitation",
    ]
    assert content_service.generate_text.await_count == 4
    assert repository_factory.topic.create.call_count == 4
    assert len(created_topics) == 4

    first_prompt = content_service.generate_text.await_args_list[0].kwargs["prompt"]
    second_prompt = content_service.generate_text.await_args_list[1].kwargs["prompt"]
    third_prompt = content_service.generate_text.await_args_list[2].kwargs["prompt"]

    assert "Week 1" in first_prompt
    assert "Topic 2 within that week" in second_prompt
    assert "Atmospheric Structure" in second_prompt
    assert "Trace Gases and Water Vapor" in third_prompt


@pytest.mark.asyncio
async def test_generate_topics_for_course_reuses_existing_slots_and_normalizes_position(
    monkeypatch,
):
    monkeypatch.setattr(
        "artificial_u.services.topic_generator_service.get_settings",
        lambda: SimpleNamespace(TOPICS_GENERATION_MODEL="test-topics-model"),
    )

    existing_topic = Topic(
        id=10,
        title="Atmospheric Structure",
        course_id=1,
        week=1,
        order=1,
    )
    service, repository_factory, content_service, _ = _build_service(
        existing_topics=[existing_topic]
    )
    content_service.generate_text.side_effect = [
        "<output><topic><title>Trace Gases and Water Vapor</title><week>99</week><order>99</order></topic></output>",
        "<output><topic><title>Radiation and Energy Balance</title><week>2</week><order>1</order></topic></output>",
        (
            "<output><topic><title>Cloud Formation and Precipitation</title>"
            "<week>2</week><order>2</order></topic></output>"
        ),
    ]

    topics = await service.generate_topics_for_course(course_id=1, created_by=7)

    assert [(topic.week, topic.order) for topic in topics] == [(1, 2), (2, 1), (2, 2)]
    assert topics[0].title == "Trace Gases and Water Vapor"
    assert content_service.generate_text.await_count == 3
    repository_factory.topic.get_by_course_week_order.assert_any_call(course_id=1, week=1, order=2)

    first_generated_prompt = content_service.generate_text.await_args_list[0].kwargs["prompt"]
    assert "Atmospheric Structure" in first_generated_prompt


@pytest.mark.asyncio
async def test_generate_topic_for_course_slot_includes_related_course_topics_context(monkeypatch):
    monkeypatch.setattr(
        "artificial_u.services.topic_generator_service.get_settings",
        lambda: SimpleNamespace(TOPICS_GENERATION_MODEL="test-topics-model"),
    )

    related_course = Course(
        id=2,
        code="ATM250",
        title="Advanced Atmospheric Dynamics",
        lectures_per_week=1,
        total_weeks=1,
    )
    related_topics = [
        Topic(
            title="Geostrophic Balance",
            course_id=2,
            week=1,
            order=1,
        )
    ]
    service, _, content_service, _ = _build_service(
        connected_course_ids=[2],
        related_courses=[related_course],
        topics_by_course_id={2: related_topics},
    )
    content_service.generate_text.return_value = (
        "<output><topic><title>Baroclinic Instability</title><week>1</week><order>1</order></topic></output>"
    )

    await service.generate_topic_for_course_slot(course_id=1, week=1, order=1, created_by=7)

    prompt = content_service.generate_text.await_args.kwargs["prompt"]
    assert "Related course topics" in prompt
    assert "Related course: Advanced Atmospheric Dynamics" in prompt
    assert "Geostrophic Balance" in prompt
