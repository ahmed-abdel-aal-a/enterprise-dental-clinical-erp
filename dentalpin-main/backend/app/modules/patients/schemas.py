"""Pydantic schemas for the patients module.

After Fase B.4 this module only owns patient identity + demographics +
billing. Medical history, emergency contact, legal guardian and alert
shapes live in ``app.modules.patients_clinical.schemas``.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# --- Billing -------------------------------------------------------------


class BillingAddress(BaseModel):
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    province: str | None = None
    country: str = "ES"


# --- Patient CRUD --------------------------------------------------------


class PatientCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    date_of_birth: date | None = None
    notes: str | None = None
    do_not_contact: bool = False
    national_id: str | None = Field(default=None, max_length=50)
    national_id_type: str | None = Field(default=None, max_length=20)
    billing_name: str | None = Field(default=None, max_length=200)
    billing_tax_id: str | None = Field(default=None, max_length=50)
    billing_address: BillingAddress | None = None
    billing_email: EmailStr | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    date_of_birth: date | None = None
    notes: str | None = None
    status: str | None = None
    do_not_contact: bool | None = None
    billing_name: str | None = Field(default=None, max_length=200)
    billing_tax_id: str | None = Field(default=None, max_length=50)
    billing_address: BillingAddress | None = None
    billing_email: EmailStr | None = None


class PatientResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    first_name: str
    last_name: str
    phone: str | None
    email: str | None
    date_of_birth: date | None
    notes: str | None
    status: str
    do_not_contact: bool
    billing_name: str | None
    billing_tax_id: str | None
    billing_address: dict | None
    billing_email: str | None
    has_complete_billing_info: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientBrief(BaseModel):
    """Brief patient info for lists and references across modules."""

    id: UUID
    first_name: str
    last_name: str
    phone: str | None
    email: str | None

    model_config = ConfigDict(from_attributes=True)


# --- Extended demographics ----------------------------------------------


class PatientAddress(BaseModel):
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    province: str | None = None
    country: str = "ES"


class PatientExtendedResponse(PatientResponse):
    gender: str | None = None
    national_id: str | None = None
    national_id_type: str | None = None
    profession: str | None = None
    workplace: str | None = None
    preferred_language: str = "es"
    address: PatientAddress | None = None
    photo_url: str | None = None


class PatientExtendedUpdate(PatientUpdate):
    gender: str | None = Field(default=None, max_length=20)
    national_id: str | None = Field(default=None, max_length=50)
    national_id_type: str | None = Field(default=None, max_length=20)
    profession: str | None = Field(default=None, max_length=100)
    workplace: str | None = Field(default=None, max_length=200)
    preferred_language: str | None = Field(default=None, max_length=10)
    address: PatientAddress | None = None
    photo_url: str | None = Field(default=None, max_length=500)


# --- First Visit Onboarding ----------------------------------------------


class InitialChargeSpec(BaseModel):
    amount: Decimal = Field(default=Decimal("200.00"), gt=0)
    description: str = Field(default="كشف أولي واستشارة وتشخيص", max_length=255)
    catalog_item_id: UUID | None = None


class InitialPaymentSpec(BaseModel):
    amount: Decimal = Field(gt=0)
    method: str = Field(default="cash")
    notes: str | None = None


class FirstVisitCreate(BaseModel):
    patient_data: PatientCreate
    branch_id: UUID | None = None
    initial_charge: InitialChargeSpec | None = None
    initial_payment: InitialPaymentSpec | None = None


class FirstVisitResponse(BaseModel):
    patient: PatientResponse
    charge_id: UUID | None = None
    payment_id: UUID | None = None
    total_charged: Decimal = Decimal("0.00")
    total_paid: Decimal = Decimal("0.00")
    remaining_balance: Decimal = Decimal("0.00")
