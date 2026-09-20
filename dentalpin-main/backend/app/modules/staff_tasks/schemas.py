"""Pydantic schemas for the staff_tasks module."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TaskStatus = Literal["open", "claimed", "done", "cancelled"]
TaskPriority = Literal["low", "normal", "high"]


class StaffTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    details: str | None = Field(default=None, max_length=5000)
    priority: TaskPriority = "normal"
    assignee_id: UUID | None = None
    due_date: date | None = None


class StaffTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    details: str | None = Field(default=None, max_length=5000)
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    assignee_id: UUID | None = None
    due_date: date | None = None


class StaffTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    title: str
    details: str | None
    status: TaskStatus
    priority: TaskPriority
    assignee_id: UUID | None
    assignee_name: str | None = None
    created_by: UUID | None
    due_date: date | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
