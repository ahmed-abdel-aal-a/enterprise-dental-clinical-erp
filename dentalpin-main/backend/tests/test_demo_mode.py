"""`DEMO_MODE=true` must block operations that would lock out or break the
shared public demo (user edits/removal, module lifecycle), while leaving the
rest of the app interactive."""

from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.config import settings
from app.core.auth.models import Clinic


@pytest.fixture
def demo_mode() -> Iterator[None]:
    settings.DEMO_MODE = True
    yield
    settings.DEMO_MODE = False


async def test_update_user_blocked(
    client: AsyncClient, auth_headers: dict[str, str], test_clinic: Clinic, demo_mode: None
) -> None:
    r = await client.put(
        f"/api/v1/auth/users/{uuid4()}",
        json={"first_name": "Hacked"},
        headers=auth_headers,
    )
    assert r.status_code == 403, r.text
    assert "demo" in r.text.lower()


async def test_delete_user_blocked(
    client: AsyncClient, auth_headers: dict[str, str], test_clinic: Clinic, demo_mode: None
) -> None:
    r = await client.delete(f"/api/v1/auth/users/{uuid4()}", headers=auth_headers)
    assert r.status_code == 403, r.text


async def test_module_lifecycle_blocked(
    client: AsyncClient, auth_headers: dict[str, str], test_clinic: Clinic, demo_mode: None
) -> None:
    for op in ("install", "uninstall", "upgrade"):
        r = await client.post(f"/api/v1/modules/schedules/{op}", headers=auth_headers)
        assert r.status_code == 403, f"{op}: {r.text}"
    r = await client.post("/api/v1/modules/-/restart", headers=auth_headers)
    assert r.status_code == 403, r.text


async def test_reads_still_work(
    client: AsyncClient, auth_headers: dict[str, str], test_clinic: Clinic, demo_mode: None
) -> None:
    r = await client.get("/api/v1/auth/users", headers=auth_headers)
    assert r.status_code == 200, r.text


async def test_flag_off_does_not_block(
    client: AsyncClient, auth_headers: dict[str, str], test_clinic: Clinic
) -> None:
    # Unknown user id → 404, i.e. the guard let the request through.
    r = await client.delete(f"/api/v1/auth/users/{uuid4()}", headers=auth_headers)
    assert r.status_code == 404, r.text
