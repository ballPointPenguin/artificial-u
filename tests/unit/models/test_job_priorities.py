"""Unit tests for the centralized job scheduling priorities."""

import pytest

from artificial_u.models.job_priorities import (
    DEFAULT_JOB_PRIORITY,
    priority_for_kind,
)


@pytest.mark.unit
def test_unknown_kind_falls_back_to_default():
    assert priority_for_kind("not_a_real_kind") == DEFAULT_JOB_PRIORITY


@pytest.mark.unit
def test_neutral_kinds_use_default():
    # Image work and lecture text generation stay at the neutral default so they
    # are not starved behind slow background work.
    for kind in (
        "generate_lecture",
        "generate_lecture_text_only",
        "generate_lecture_images",
        "generate_lecture_slide",
        "generate_topics_for_course",
    ):
        assert priority_for_kind(kind) == DEFAULT_JOB_PRIORITY


@pytest.mark.unit
def test_slow_background_work_is_demoted_below_default():
    # Audio is the slowest, most rate-limited step and must run after fast jobs.
    audio = priority_for_kind("generate_lecture_audio")
    timeline = priority_for_kind("generate_lecture_timeline")
    assert audio < DEFAULT_JOB_PRIORITY
    assert timeline < DEFAULT_JOB_PRIORITY
    # Audio is the lowest priority of all.
    assert audio < timeline
