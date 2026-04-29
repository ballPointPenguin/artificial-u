"""Unit tests for TopicService deletion behavior."""

from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from artificial_u.services.topic_service import TopicService


@pytest.fixture
def repository_factory():
    factory = MagicMock()
    factory.topic = MagicMock()
    return factory


@pytest.fixture
def lecture_service():
    return MagicMock()


@pytest.mark.unit
def test_delete_topic_deletes_topic_lectures_first(repository_factory, lecture_service):
    lecture_service.list_lectures.return_value = [
        SimpleNamespace(id=10),
        SimpleNamespace(id=11),
    ]
    repository_factory.topic.delete.return_value = True
    service = TopicService(
        repository_factory=repository_factory,
        lecture_service=lecture_service,
    )

    assert service.delete_topic(1) is True

    lecture_service.list_lectures.assert_called_once_with(topic_id=1)
    assert lecture_service.delete_lecture.call_args_list == [
        call(10),
        call(11),
    ]
    repository_factory.topic.delete.assert_called_once_with(1)


@pytest.mark.unit
def test_delete_topic_skips_lecture_without_id(repository_factory, lecture_service):
    lecture_service.list_lectures.return_value = [
        SimpleNamespace(id=None),
        SimpleNamespace(id=12),
    ]
    repository_factory.topic.delete.return_value = True
    service = TopicService(
        repository_factory=repository_factory,
        lecture_service=lecture_service,
    )

    assert service.delete_topic(1) is True

    lecture_service.delete_lecture.assert_called_once_with(12)
    repository_factory.topic.delete.assert_called_once_with(1)
