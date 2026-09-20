"""RFC 5545 export of a single appointment (issue #129).

Hand-rolled on purpose: one ``VEVENT`` is ~25 lines of string building
and does not justify an ``icalendar`` dependency. The RFC details that
actually bite are handled here — CRLF line endings, 75-octet line
folding, escaping of ``, ; \\`` and newlines in text values, UTC
``...Z`` timestamps, and a stable ``UID``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.auth.models import Clinic

    from .models import Appointment

PRODID = "-//DentApex//Agenda//EN"
UID_DOMAIN = "dentapex.com"

# Appointment statuses that map to a cancelled VEVENT; everything else
# ships as CONFIRMED (calendar clients have no richer vocabulary).
_CANCELLED_STATUSES = {"cancelled", "no_show"}


def _escape(value: str) -> str:
    """Escape a TEXT value per RFC 5545 §3.3.11."""
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> list[str]:
    """Fold a content line at 75 octets (continuation lines start with a space)."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return [line]
    out: list[str] = []
    rest = encoded
    first = True
    while rest:
        limit = 75 if first else 74  # continuation lines lose one octet to the space
        chunk = rest[:limit]
        # Never split inside a UTF-8 multi-byte sequence.
        while chunk and (chunk[-1] & 0xC0) == 0x80:
            chunk = chunk[:-1]
        out.append(("" if first else " ") + chunk.decode("utf-8"))
        rest = rest[len(chunk) :]
        first = False
    return out


def _utc(dt: datetime) -> str:
    """Render an aware datetime as an RFC 5545 UTC timestamp (``...Z``)."""
    return dt.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _location(clinic: Clinic) -> str:
    address = clinic.address or {}
    parts = [clinic.name]
    for key in ("street", "city", "postal_code"):
        value = address.get(key)
        if value:
            parts.append(str(value))
    return ", ".join(parts)


def build_appointment_ics(
    appointment: Appointment,
    clinic: Clinic,
    *,
    now: datetime | None = None,
) -> str:
    """A complete single-``VEVENT`` iCalendar document, CRLF-terminated.

    ``SUMMARY``/``DESCRIPTION`` carry no clinical detail beyond what the
    appointment already shows: treatment type and the people involved.
    ``now`` is injectable for deterministic tests.
    """
    stamp = _utc(now if now is not None else datetime.now(UTC))

    summary = appointment.treatment_type or "Dental appointment"

    description_parts: list[str] = []
    if appointment.patient is not None:
        description_parts.append(
            f"Patient: {appointment.patient.first_name} {appointment.patient.last_name}"
        )
    if appointment.professional is not None:
        description_parts.append(
            f"Professional: {appointment.professional.first_name} "
            f"{appointment.professional.last_name}"
        )

    status = "CANCELLED" if appointment.status in _CANCELLED_STATUSES else "CONFIRMED"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{appointment.id}@{UID_DOMAIN}",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{_utc(appointment.start_time)}",
        f"DTEND:{_utc(appointment.end_time)}",
        f"SUMMARY:{_escape(summary)}",
    ]
    if description_parts:
        lines.append(f"DESCRIPTION:{_escape(chr(10).join(description_parts))}")
    lines.append(f"LOCATION:{_escape(_location(clinic))}")
    lines.append(f"STATUS:{status}")
    lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")

    folded: list[str] = []
    for line in lines:
        folded.extend(_fold(line))
    return "\r\n".join(folded) + "\r\n"
