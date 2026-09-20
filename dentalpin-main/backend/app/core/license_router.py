"""License management API endpoints for DentApex Arabic Edition."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.license import (
    activate_license,
    get_cached_license_state,
)

router = APIRouter(prefix="/license", tags=["License"])


class LicenseActivateRequest(BaseModel):
    license_key: str = Field(..., min_length=15, max_length=30, description="DP-XXXX-XXXX-XXXX-XXXX")
    clinic_name: str = Field(..., min_length=2, max_length=200, description="اسم العيادة المرخص لها")


class LicenseStatusResponse(BaseModel):
    status: str
    days_left: int | None = None
    hw_fingerprint: str
    clinic_name: str | None = None
    is_operational_allowed: bool
    message: str


@router.get("/status", response_model=LicenseStatusResponse)
async def get_license_status() -> LicenseStatusResponse:
    """Retrieve current license & trial status from zero-cost in-memory cache."""
    state = get_cached_license_state()
    return LicenseStatusResponse(
        status=state["status"],
        days_left=state.get("days_left"),
        hw_fingerprint=state["hw_fingerprint"],
        clinic_name=state.get("clinic_name"),
        is_operational_allowed=state.get("is_operational_allowed", True),
        message=state.get("message", ""),
    )


@router.post("/activate")
async def activate_system_license(data: LicenseActivateRequest) -> dict:
    """Activate permanent license key for this clinic and hardware."""
    result = activate_license(
        license_key=data.license_key.strip(),
        clinic_name=data.clinic_name.strip(),
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "كود التفعيل غير صالح"),
        )
    return result
