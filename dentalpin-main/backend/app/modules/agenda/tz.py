"""Clinic-timezone helpers for appointment datetime semantics (issue #161).

Contract: naive datetimes entering the module are **clinic-local wall-clock**
(the receptionist books "11:00" in the clinic's timezone, whatever the
browser). Aware datetimes are instants and pass through. Everything is
persisted as UTC; API responses serialize ``start_time``/``end_time`` back
in the clinic timezone so wall-clock consumers (calendar grid) and instant
consumers (``new Date()`` on the dashboard) both read correctly.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic

logger = logging.getLogger(__name__)

DEFAULT_TIMEZONE = "Africa/Cairo"


def safe_zone(tz_name: str | None) -> ZoneInfo:
    """Resolve an IANA id defensively — DB hand-edits must not 500 the agenda."""
    try:
        return ZoneInfo(tz_name or DEFAULT_TIMEZONE)
    except ZoneInfoNotFoundError:
        logger.warning("Invalid timezone %r; falling back to %s", tz_name, DEFAULT_TIMEZONE)
        return ZoneInfo(DEFAULT_TIMEZONE)


async def get_clinic_tz(db: AsyncSession, clinic_id: UUID) -> ZoneInfo:
    result = await db.execute(select(Clinic.timezone).where(Clinic.id == clinic_id))
    return safe_zone(result.scalar_one_or_none())


def as_utc(dt: datetime, tz: ZoneInfo) -> datetime:
    """Naive → attach clinic tz; aware → keep instant. Always return UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(UTC)
