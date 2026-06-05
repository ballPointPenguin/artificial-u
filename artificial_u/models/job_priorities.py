"""
Centralized job scheduling priorities.

Jobs are reserved in ``priority DESC, id ASC`` order (see
``JobRepository.reserve_one_skip_locked_atomic``), so a *higher* number is
scheduled sooner and ties fall back to FIFO by id.

Priority is derived from the job *kind* rather than passed around per call. This
keeps the scheme defined in one place and—critically—keeps it consistent across
follow-up chains: a chained ``generate_lecture_audio`` job is scheduled with the
same priority whether it was enqueued directly or as the tail of a batch.

Design intent
-------------
The worker pool is small (``WORKER_MAX_CONCURRENCY``), so a few slow,
rate-limited jobs can starve the many quick jobs behind them. We therefore keep
most work at the neutral default and *demote* the slow, long-running steps so
fast jobs (e.g. image slides) are not blocked behind them.
"""

# Neutral baseline. Most kinds run here, ordered FIFO by id.
DEFAULT_JOB_PRIORITY = 0

# Negative = run after the neutral default; positive = run before it.
_JOB_PRIORITIES: dict[str, int] = {
    # Audio is the slowest and most rate-limited step (TTS). Let everything else
    # go first so a long audio job doesn't block batches of quick image jobs.
    "generate_lecture_audio": -20,
    # Forced-alignment timelines are also slow and depend on audio; keep them
    # below the neutral default but above audio.
    "generate_lecture_timeline": -10,
}


def priority_for_kind(kind: str) -> int:
    """Return the scheduling priority for a job ``kind``.

    Unknown / unlisted kinds fall back to the neutral default.
    """
    return _JOB_PRIORITIES.get(kind, DEFAULT_JOB_PRIORITY)
