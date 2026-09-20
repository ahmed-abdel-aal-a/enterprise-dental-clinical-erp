"""Pydantic schemas for Clinic Branch management."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class BranchAddress(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    street: str = Field(default="", max_length=255)
    city: str = Field(default="", max_length=100)
    state: str = Field(default="", max_length=100, validation_alias=AliasChoices("state", "province"))
    postal_code: str = Field(default="", max_length=20)
    country: str = Field(default="", max_length=100)
    map_link: str = Field(default="", max_length=500)


class BranchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Branch display name")
    code: str = Field(..., min_length=1, max_length=20, description="Unique short branch code")
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    address: BranchAddress = Field(default_factory=BranchAddress)
    is_main: bool = Field(default=False)
    is_active: bool = Field(default=True)
    display_order: int = Field(default=0)
    settings: dict = Field(default_factory=dict)


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, min_length=1, max_length=20)
    phone: str | None = None
    email: str | None = None
    address: BranchAddress | None = None
    is_main: bool | None = None
    is_active: bool | None = None
    display_order: int | None = None
    settings: dict | None = None


class BranchResponse(BranchBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    created_at: datetime
    updated_at: datetime
