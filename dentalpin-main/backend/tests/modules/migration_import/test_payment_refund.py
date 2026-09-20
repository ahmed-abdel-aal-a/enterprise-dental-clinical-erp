"""Refund target resolution.

Pure unit-style coverage of ``PaymentMapper._resolve_refund_target``
and ``_ensure_refund_target_index``: the negative-PagoCli path that
attaches refunds to either the explicit ``IdPagoCliRelacionado`` chain
or — when absent — the first positive payment booked against the same
``applied_treatment_uuid``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import pytest

from app.modules.migration_import.mappers.payment import PaymentMapper


@dataclass
class _StubResolver:
    _store: dict[tuple[str, str], Any] = field(default_factory=dict)

    async def get(self, entity_type: str, canonical_uuid: str):
        return self._store.get((entity_type, canonical_uuid))

    def preset(self, entity_type: str, canonical_uuid: str, value: Any) -> None:
        self._store[(entity_type, canonical_uuid)] = value


@dataclass
class _StubHandle:
    payments: list[dict[str, Any]]

    def entity_iter(self, entity_type: str):
        assert entity_type == "payment"
        for p in self.payments:
            yield (
                p["canonical_uuid"],
                p.get("source_id", "0"),
                "gesden",
                json.dumps(p["payload"]),
                "{}",
                None,
            )


@dataclass
class _StubCtx:
    resolver: _StubResolver = field(default_factory=_StubResolver)
    handle: _StubHandle | None = None


@pytest.mark.asyncio
async def test_resolves_via_related_payment_uuid_when_present() -> None:
    """Explicit IdPagoCliRelacionado chain wins over the fallback —
    don't waste a DPMF scan when the source gives us the link."""
    target_payment_id = uuid4()
    related = str(uuid4())
    ctx = _StubCtx()
    ctx.resolver.preset("payment", related, target_payment_id)

    mapper = PaymentMapper()
    result = await mapper._resolve_refund_target(
        ctx,  # type: ignore[arg-type]
        {"related_payment_uuid": related, "applied_treatment_uuid": str(uuid4())},
    )
    assert result == target_payment_id


@pytest.mark.asyncio
async def test_falls_back_to_applied_treatment_index() -> None:
    """When IdPagoCliRelacionado is null we recover by matching the
    refund's IdentTM to the first positive PagoCli booked against the
    same TtosMed."""
    target_payment_id = uuid4()
    at_uuid = str(uuid4())
    positive_canonical = str(uuid4())
    handle = _StubHandle(
        payments=[
            {
                "canonical_uuid": positive_canonical,
                "payload": {"amount": "100.00", "applied_treatment_uuid": at_uuid},
            },
            {
                "canonical_uuid": str(uuid4()),
                "payload": {"amount": "-50.00", "applied_treatment_uuid": at_uuid},
            },
        ]
    )
    ctx = _StubCtx(handle=handle)
    ctx.resolver.preset("payment", positive_canonical, target_payment_id)

    mapper = PaymentMapper()
    result = await mapper._resolve_refund_target(
        ctx,  # type: ignore[arg-type]
        {"applied_treatment_uuid": at_uuid},
    )
    assert result == target_payment_id


@pytest.mark.asyncio
async def test_index_skips_negative_payments() -> None:
    """A negative PagoCli must NOT itself be picked as the refund
    target — that would create circular Refund→Refund attachments."""
    at_uuid = str(uuid4())
    handle = _StubHandle(
        payments=[
            {
                "canonical_uuid": str(uuid4()),
                "payload": {"amount": "-30.00", "applied_treatment_uuid": at_uuid},
            }
        ]
    )
    ctx = _StubCtx(handle=handle)
    mapper = PaymentMapper()
    result = await mapper._resolve_refund_target(
        ctx,  # type: ignore[arg-type]
        {"applied_treatment_uuid": at_uuid},
    )
    assert result is None


@pytest.mark.asyncio
async def test_returns_none_when_neither_signal_resolves() -> None:
    ctx = _StubCtx(handle=_StubHandle(payments=[]))
    mapper = PaymentMapper()
    result = await mapper._resolve_refund_target(
        ctx,  # type: ignore[arg-type]
        {"applied_treatment_uuid": str(uuid4())},
    )
    assert result is None


@pytest.mark.asyncio
async def test_index_first_positive_wins_for_same_treatment() -> None:
    """Two positives against the same treatment → first one anchors
    the refund. Keeps the chain deterministic across re-runs."""
    at_uuid = str(uuid4())
    first_canonical = str(uuid4())
    second_canonical = str(uuid4())
    first_payment_id = uuid4()
    second_payment_id = uuid4()
    handle = _StubHandle(
        payments=[
            {
                "canonical_uuid": first_canonical,
                "payload": {"amount": "100.00", "applied_treatment_uuid": at_uuid},
            },
            {
                "canonical_uuid": second_canonical,
                "payload": {"amount": "200.00", "applied_treatment_uuid": at_uuid},
            },
        ]
    )
    ctx = _StubCtx(handle=handle)
    ctx.resolver.preset("payment", first_canonical, first_payment_id)
    ctx.resolver.preset("payment", second_canonical, second_payment_id)

    mapper = PaymentMapper()
    result = await mapper._resolve_refund_target(
        ctx,  # type: ignore[arg-type]
        {"applied_treatment_uuid": at_uuid},
    )
    assert result == first_payment_id
