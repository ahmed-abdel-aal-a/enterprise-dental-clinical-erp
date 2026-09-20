"""Staff tasks HTTP surface. Mounts under ``/api/v1/staff_tasks/*``."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .schemas import StaffTaskCreate, StaffTaskResponse, StaffTaskUpdate
from .service import StaffTaskService

router = APIRouter()


@router.get("/", response_model=PaginatedApiResponse[StaffTaskResponse])
async def list_tasks(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("staff_tasks.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    task_status: str | None = Query(default=None),
    assignee_id: UUID | None = Query(default=None),
    due_before: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedApiResponse[StaffTaskResponse]:
    tasks, total = await StaffTaskService.list_tasks(
        db,
        ctx.clinic_id,
        task_status=task_status,
        assignee_id=assignee_id,
        due_before=due_before,
        page=page,
        page_size=page_size,
    )
    return PaginatedApiResponse(
        data=[StaffTaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=ApiResponse[StaffTaskResponse])
async def get_task(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("staff_tasks.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    task_id: UUID,
) -> ApiResponse[StaffTaskResponse]:
    task = await StaffTaskService.get_task(db, ctx.clinic_id, task_id)
    return ApiResponse(data=StaffTaskResponse.model_validate(task))


@router.post(
    "/", response_model=ApiResponse[StaffTaskResponse], status_code=status.HTTP_201_CREATED
)
async def create_task(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("staff_tasks.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: StaffTaskCreate,
) -> ApiResponse[StaffTaskResponse]:
    task = await StaffTaskService.create_task(db, ctx.clinic_id, payload, ctx.user_id)
    return ApiResponse(data=StaffTaskResponse.model_validate(task))


@router.patch("/{task_id}", response_model=ApiResponse[StaffTaskResponse])
async def update_task(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("staff_tasks.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    task_id: UUID,
    payload: StaffTaskUpdate,
) -> ApiResponse[StaffTaskResponse]:
    task = await StaffTaskService.update_task(db, ctx.clinic_id, task_id, payload, ctx.user_id)
    return ApiResponse(data=StaffTaskResponse.model_validate(task))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("staff_tasks.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    task_id: UUID,
) -> None:
    await StaffTaskService.delete_task(db, ctx.clinic_id, task_id)
