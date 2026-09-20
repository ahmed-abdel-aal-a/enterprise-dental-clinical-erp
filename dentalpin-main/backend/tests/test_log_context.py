"""Per-request log context: contextvars + middleware + log filter."""

from __future__ import annotations

import logging

import pytest
from httpx import AsyncClient

from app.core.log_context import (
    CLINIC_ID,
    REQUEST_ID,
    USER_ID,
    LogContextFilter,
    bind,
    get_request_id,
    new_request_id,
    reset_request_context,
    set_request_context,
)


def test_new_request_id_is_short_hex() -> None:
    rid = new_request_id()
    assert len(rid) == 16
    assert all(c in "0123456789abcdef" for c in rid)


def test_default_values_are_dash() -> None:
    # Outside any binding, the trio should be unbound (``-``). A fresh
    # asyncio task starts from the module-level defaults.
    assert REQUEST_ID.get() == "-"
    assert CLINIC_ID.get() == "-"
    assert USER_ID.get() == "-"


def test_set_and_reset_restores_previous_value() -> None:
    tokens = set_request_context(request_id="abc", clinic_id="111", user_id="222")
    assert get_request_id() == "abc"
    assert CLINIC_ID.get() == "111"
    assert USER_ID.get() == "222"
    reset_request_context(tokens)
    assert get_request_id() == "-"
    assert CLINIC_ID.get() == "-"
    assert USER_ID.get() == "-"


def test_bind_context_manager_resets_on_exit() -> None:
    with bind(request_id="req-1", clinic_id="c1"):
        assert get_request_id() == "req-1"
        assert CLINIC_ID.get() == "c1"
    assert get_request_id() == "-"
    assert CLINIC_ID.get() == "-"


def test_log_filter_attaches_current_values(caplog: pytest.LogCaptureFixture) -> None:
    """LogRecord should get ``request_id`` / ``clinic_id`` / ``user_id``
    attributes from the contextvars, so formatters can render them."""
    log = logging.getLogger("test.log_context")
    log.addFilter(LogContextFilter())
    with bind(request_id="r-9", clinic_id="c-9", user_id="u-9"), caplog.at_level(logging.INFO):
        log.info("hello")
    record = next(r for r in caplog.records if r.message == "hello")
    assert record.request_id == "r-9"
    assert record.clinic_id == "c-9"
    assert record.user_id == "u-9"


def test_log_filter_respects_explicit_extra(caplog: pytest.LogCaptureFixture) -> None:
    """Explicit ``extra={"clinic_id": ...}`` overrides the contextvar so
    a publisher with a payload-side clinic id keeps it."""
    log = logging.getLogger("test.log_context_explicit")
    log.addFilter(LogContextFilter())
    with bind(clinic_id="ctxvar-clinic"), caplog.at_level(logging.INFO):
        log.info("payload event", extra={"clinic_id": "explicit-clinic"})
    record = next(r for r in caplog.records if r.message == "payload event")
    assert record.clinic_id == "explicit-clinic"


@pytest.mark.asyncio
async def test_middleware_generates_request_id_when_missing(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    rid = response.headers.get("x-request-id")
    assert rid is not None
    assert len(rid) == 16


@pytest.mark.asyncio
async def test_middleware_echoes_inbound_request_id(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-Id": "trace-1234"})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "trace-1234"
