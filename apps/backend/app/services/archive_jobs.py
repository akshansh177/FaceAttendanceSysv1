"""Nightly archive job stub — move old attendance_logs partitions per ops runbook."""

from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

ARCHIVE_MONTHS = 24


async def run_archive_job(db: AsyncSession) -> dict:
    """Placeholder: logs partitions older than ARCHIVE_MONTHS should be archived manually."""
    cutoff = date.today().replace(day=1) - timedelta(days=ARCHIVE_MONTHS * 30)
    logger.info("Archive job stub: partitions before %s — see docker/scripts/partition-attendance-logs.sql", cutoff)
    return {"status": "stub", "cutoff": cutoff.isoformat(), "archived_rows": 0}
