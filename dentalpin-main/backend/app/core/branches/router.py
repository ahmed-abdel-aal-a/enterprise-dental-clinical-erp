"""FastAPI router for Clinic Branch management."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.branches.schemas import BranchCreate, BranchResponse, BranchUpdate
from app.core.branches.service import BranchService
from app.core.schemas import ApiResponse
from app.database import get_db

router = APIRouter(prefix="/branches", tags=["branches"])


@router.get("", response_model=ApiResponse[list[BranchResponse]])
async def list_branches(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = Query(default=False, description="Filter active branches only"),
) -> ApiResponse[list[BranchResponse]]:
    """List all branches for the authenticated clinic."""
    branches = await BranchService.list_branches(db, ctx.clinic_id, active_only=active_only)
    return ApiResponse(data=[BranchResponse.model_validate(b) for b in branches])


@router.get("/{branch_id}", response_model=ApiResponse[BranchResponse])
async def get_branch(
    branch_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BranchResponse]:
    """Get details of a specific branch."""
    branch = await BranchService.get_branch(db, ctx.clinic_id, branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return ApiResponse(data=BranchResponse.model_validate(branch))


@router.post(
    "",
    response_model=ApiResponse[BranchResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin.clinic.write"))],
)
async def create_branch(
    data: BranchCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BranchResponse]:
    """Create a new branch for the clinic."""
    try:
        branch = await BranchService.create_branch(db, ctx.clinic_id, data)
        return ApiResponse(data=BranchResponse.model_validate(branch))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create branch: {exc}",
        )


@router.put(
    "/{branch_id}",
    response_model=ApiResponse[BranchResponse],
    dependencies=[Depends(require_permission("admin.clinic.write"))],
)
@router.patch(
    "/{branch_id}",
    response_model=ApiResponse[BranchResponse],
    dependencies=[Depends(require_permission("admin.clinic.write"))],
)
async def update_branch(
    branch_id: UUID,
    data: BranchUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BranchResponse]:
    """Update branch details."""
    branch = await BranchService.update_branch(db, ctx.clinic_id, branch_id, data)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return ApiResponse(data=BranchResponse.model_validate(branch))


@router.delete(
    "/{branch_id}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_permission("admin.clinic.write"))],
)
async def delete_branch(
    branch_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[bool]:
    """Soft delete (deactivate) a branch safely."""
    success = await BranchService.delete_branch(db, ctx.clinic_id, branch_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return ApiResponse(data=True)
