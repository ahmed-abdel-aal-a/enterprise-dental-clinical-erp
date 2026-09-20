"""DentApex Vault HTTP Router - Clinical snapshot export and R2 sync endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context
from app.config import settings
from app.core.r2_vault import VaultSnapshotService, encrypt_payload
from app.core.schemas import ApiResponse
from app.database import get_db

router = APIRouter(prefix="/vault", tags=["vault"])


@router.get("/snapshot")
async def get_vault_snapshot(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_vault_passphrase: Annotated[str | None, Header()] = None,
    encrypted: bool = True,
):
    """Generate and return clinical snapshot. If encrypted=True, returns AES-256-GCM binary."""
    snapshot = await VaultSnapshotService.build_snapshot(db, ctx.clinic_id)
    if not encrypted:
        return ApiResponse(data=snapshot)

    secret = x_vault_passphrase or settings.SECRET_KEY
    blob = encrypt_payload(snapshot, secret)
    return Response(
        content=blob,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="dentapex_vault_{ctx.clinic_id}.enc"',
            "X-DentApex-Vault-Version": "1.0.0",
        },
    )
