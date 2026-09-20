"""DentApex R2 Encrypted Vault - Portable Database Snapshot & Encryption Engine.

Produces compact clinical snapshots, encrypts them with AES-256-GCM using clinic
master key, and provides push capabilities to Cloudflare Edge Worker Gateway.
Zero-knowledge: server and cloud never see plaintext without the master key.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.branches.models import ClinicBranch
from app.modules.agenda.models import Appointment, Cabinet
from app.modules.catalog.models import TreatmentCatalogItem
from app.modules.patients.models import Patient

MAGIC_HEADER = b"DPAX"  # DentApex Vault Magic Signature


def derive_key(secret: str, salt: bytes) -> bytes:
    """Derive 256-bit AES key using PBKDF2-HMAC-SHA256 with 100,000 rounds."""
    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return kdf.derive(secret.encode("utf-8"))


def encrypt_payload(data: dict, secret: str) -> bytes:
    """Serialize dictionary to JSON and encrypt with AES-256-GCM.

    Envelope format:
    MAGIC (4 bytes) | SALT (16 bytes) | IV (12 bytes) | CIPHERTEXT + TAG (AESGCM)
    """
    json_bytes = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
    salt = os.urandom(16)
    key = derive_key(secret, salt)
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ciphertext_with_tag = aesgcm.encrypt(iv, json_bytes, associated_data=MAGIC_HEADER)
    return MAGIC_HEADER + salt + iv + ciphertext_with_tag


def decrypt_payload(encrypted_blob: bytes, secret: str) -> dict:
    """Decrypt AES-256-GCM encrypted envelope back to python dictionary."""
    if len(encrypted_blob) < 36 or not encrypted_blob.startswith(MAGIC_HEADER):
        raise ValueError("Invalid DentApex Vault payload header or truncated file")

    offset = len(MAGIC_HEADER)
    salt = encrypted_blob[offset : offset + 16]
    offset += 16
    iv = encrypted_blob[offset : offset + 12]
    offset += 12
    ciphertext = encrypted_blob[offset:]

    key = derive_key(secret, salt)
    aesgcm = AESGCM(key)
    decrypted_bytes = aesgcm.decrypt(iv, ciphertext, associated_data=MAGIC_HEADER)
    return json.loads(decrypted_bytes.decode("utf-8"))


class VaultSnapshotService:
    """Builds and manages clinical snapshots for offline mobile hydration."""

    @staticmethod
    async def build_snapshot(db: AsyncSession, clinic_id: UUID) -> dict:
        """Export compact JSON of active clinic data for 24/7 mobile offline use."""
        now = datetime.now(UTC)
        window_start = now - timedelta(days=30)
        window_end = now + timedelta(days=60)

        # 1. Fetch Patients
        pat_stmt = (
            select(Patient)
            .where(Patient.clinic_id == clinic_id, Patient.status != "archived")
            .order_by(Patient.last_name, Patient.first_name)
        )
        patients_res = await db.execute(pat_stmt)
        patients = [
            {
                "id": str(p.id),
                "first_name": p.first_name,
                "last_name": p.last_name,
                "full_name": f"{p.first_name} {p.last_name}".strip(),
                "phone": p.phone or "",
                "email": p.email or "",
                "national_id": p.national_id or "",
                "gender": p.gender or "",
            }
            for p in patients_res.scalars().all()
        ]

        # 2. Fetch Appointments within 90-day window
        apt_stmt = (
            select(Appointment)
            .options(selectinload(Appointment.patient))
            .where(
                Appointment.clinic_id == clinic_id,
                Appointment.start_time >= window_start,
                Appointment.start_time <= window_end,
                Appointment.status.notin_(["cancelled"]),
            )
            .order_by(Appointment.start_time.asc())
        )
        apt_res = await db.execute(apt_stmt)
        appointments = [
            {
                "id": str(a.id),
                "patient_id": str(a.patient_id) if a.patient_id else None,
                "patient_name": (
                    f"{a.patient.first_name} {a.patient.last_name}".strip()
                    if a.patient
                    else "مريض غير محدد"
                ),
                "professional_id": str(a.professional_id) if a.professional_id else None,
                "cabinet_id": str(a.cabinet_id) if a.cabinet_id else None,
                "cabinet": a.cabinet or "",
                "start_time": a.start_time.isoformat(),
                "end_time": a.end_time.isoformat(),
                "status": a.status,
                "treatment_type": a.treatment_type or "",
                "color": a.color or "",
            }
            for a in apt_res.scalars().all()
        ]

        # 3. Fetch Cabinets
        cab_stmt = select(Cabinet).where(Cabinet.clinic_id == clinic_id, Cabinet.is_active.is_(True))
        cab_res = await db.execute(cab_stmt)
        cabinets = [{"id": str(c.id), "name": c.name, "branch_id": str(c.branch_id) if c.branch_id else None} for c in cab_res.scalars().all()]

        # 4. Fetch Branches
        branch_stmt = select(ClinicBranch).where(ClinicBranch.clinic_id == clinic_id, ClinicBranch.is_active.is_(True))
        branch_res = await db.execute(branch_stmt)
        branches = [{"id": str(b.id), "name": b.name, "is_main": b.is_main} for b in branch_res.scalars().all()]

        # 5. Fetch Treatment Catalog
        cat_stmt = select(TreatmentCatalogItem).where(TreatmentCatalogItem.clinic_id == clinic_id, TreatmentCatalogItem.is_active.is_(True))
        cat_res = await db.execute(cat_stmt)
        catalog = [
            {
                "id": str(ct.id),
                "name": ct.names.get("ar") or ct.names.get("en") or ct.internal_code or "خدمة علاجية",
                "price": float(ct.default_price or 0),
                "duration": ct.default_duration_minutes or 30,
                "category_id": str(ct.category_id) if ct.category_id else None,
            }
            for ct in cat_res.scalars().all()
        ]

        return {
            "version": "1.0.0",
            "system": "DentApex Arabic Edition",
            "clinic_id": str(clinic_id),
            "generated_at": now.isoformat(),
            "window": {"start": window_start.isoformat(), "end": window_end.isoformat()},
            "patients": patients,
            "appointments": appointments,
            "cabinets": cabinets,
            "branches": branches,
            "catalog": catalog,
        }
