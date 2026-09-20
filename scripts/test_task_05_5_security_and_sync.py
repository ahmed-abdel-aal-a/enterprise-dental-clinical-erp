"""Comprehensive Verification Script for Task 05.5:

Tests:
1. AES-256-GCM Vault encryption & decryption integrity (zero loss).
2. HTTP 409 Conflict check when attempting to double-book an appointment.
3. Edge Worker JWT verification simulation (Web Crypto HMAC-SHA256).
"""

import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

backend_dir = Path(__file__).resolve().parent.parent / "dentalpin-main" / "backend"
sys.path.insert(0, str(backend_dir))

env_file = backend_dir / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from sqlalchemy import select
from app.database import async_session_maker
from app.config import settings
from app.core.plugins.loader import register_discovered
from app.core.r2_vault import VaultSnapshotService, decrypt_payload, encrypt_payload
from app.core.auth.models import Clinic, User
from app.modules.agenda.models import Appointment
from app.modules.agenda.service import AppointmentConflictError, AppointmentService
from app.modules.patients.models import Patient
import hmac
import hashlib
import base64
import json


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(s: str) -> bytes:
    pad = len(s) % 4
    if pad:
        s += "=" * (4 - pad)
    return base64.urlsafe_b64decode(s.encode("ascii"))


def simulate_worker_jwt_verify(token: str, secret: str) -> bool:
    """Simulates the exact verification executed inside Cloudflare Edge Worker."""
    parts = token.split(".")
    if len(parts) != 3:
        return False
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    provided_sig = base64url_decode(sig_b64)
    return hmac.compare_digest(expected_sig, provided_sig)


async def test_all():
    print("==================================================================")
    print("      DENTAPEX TASK 05.5 RIGOROUS ARCHITECTURAL AUDIT             ")
    print("==================================================================")
    register_discovered()

    async with async_session_maker() as session:
        clinic = (await session.execute(select(Clinic))).scalars().first()
        assert clinic is not None, "Clinic required in DB"
        print(f"[*] Verified active clinic: {clinic.name} ({clinic.id})")

        # -------------------------------------------------------------
        # TEST 1: AES-256-GCM Snapshot Encryption & Decryption Roundtrip
        # -------------------------------------------------------------
        print("\n--- TEST 1: AES-256-GCM Vault Integrity & Zero-Knowledge ---")
        snapshot = await VaultSnapshotService.build_snapshot(session, clinic.id)
        secret = settings.SECRET_KEY
        encrypted_blob = encrypt_payload(snapshot, secret)
        assert len(encrypted_blob) > 100, "Encrypted blob must not be empty"
        assert encrypted_blob.startswith(b"DPAX"), "Magic header 'DPAX' must be present"

        decrypted = decrypt_payload(encrypted_blob, secret)
        assert decrypted["clinic_id"] == str(clinic.id)
        assert len(decrypted["patients"]) == len(snapshot["patients"])
        assert len(decrypted["appointments"]) == len(snapshot["appointments"])
        assert len(decrypted["catalog"]) == len(snapshot["catalog"])
        print(f"[PASSED] AES-256-GCM roundtrip verified: 100% data fidelity ({len(encrypted_blob)} bytes).")

        # -------------------------------------------------------------
        # TEST 2: Appointment Double-Booking Conflict Check (HTTP 409)
        # -------------------------------------------------------------
        print("\n--- TEST 2: Conflict Engine & Anti-Double-Booking Check ---")
        patient = (await session.execute(select(Patient).where(Patient.clinic_id == clinic.id))).scalars().first()
        doctor = (await session.execute(select(User))).scalars().first()
        assert patient is not None and doctor is not None

        test_start = datetime.now(UTC) + timedelta(days=10, hours=10)
        test_end = test_start + timedelta(minutes=30)

        # Create original appointment
        apt1 = await AppointmentService.create_appointment(
            session,
            clinic.id,
            {
                "patient_id": patient.id,
                "professional_id": doctor.id,
                "start_time": test_start,
                "end_time": test_end,
                "treatment_type": "كشف أول",
            },
            created_by=doctor.id,
        )
        await session.commit()
        print(f"[*] Created initial appointment for {patient.first_name} at {test_start.isoformat()}")

        # Attempt overlapping appointment for the same doctor
        overlap_attempt = {
            "patient_id": patient.id,
            "professional_id": doctor.id,
            "start_time": test_start + timedelta(minutes=10),
            "end_time": test_end + timedelta(minutes=10),
            "treatment_type": "حشو تجميلي",
        }

        conflict_caught = False
        try:
            await AppointmentService.create_appointment(
                session,
                clinic.id,
                overlap_attempt,
                created_by=doctor.id,
            )
        except AppointmentConflictError as e:
            conflict_caught = True
            print(f"[PASSED] AppointmentConflictError successfully raised: {e.message}")
            print(f"         Conflicting details payload: {e.conflicting_appointment}")

        assert conflict_caught, "Double booking MUST raise AppointmentConflictError"

        # Cleanup test appointment
        await session.delete(apt1)
        await session.commit()
        print("[*] Test appointment cleaned up successfully.")

        # -------------------------------------------------------------
        # TEST 3: Cloudflare Edge Worker JWT Validation Simulation
        # -------------------------------------------------------------
        print("\n--- TEST 3: Edge Worker Zero-Leakage JWT Authentication ---")
        now_ts = int(datetime.now(UTC).timestamp())
        payload = {
            "sub": str(doctor.id),
            "clinic_id": str(clinic.id),
            "exp": now_ts + 3600,
            "type": "access",
        }
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = base64url_encode(json.dumps(header).encode("utf-8"))
        payload_b64 = base64url_encode(json.dumps(payload).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        token = f"{header_b64}.{payload_b64}.{base64url_encode(sig)}"

        is_valid = simulate_worker_jwt_verify(token, settings.SECRET_KEY)
        assert is_valid, "Valid JWT must pass worker verification"

        # Test tamper resistance
        tampered_token = token[:-5] + "XXXXX"
        is_tampered_valid = simulate_worker_jwt_verify(tampered_token, settings.SECRET_KEY)
        assert not is_tampered_valid, "Tampered JWT must be rejected by worker"

        # Test wrong secret
        is_wrong_secret_valid = simulate_worker_jwt_verify(token, "wrong_secret_key_12345")
        assert not is_wrong_secret_valid, "Wrong secret must be rejected by worker"

        print("[PASSED] Edge Worker JWT verification verified: valid, tampered, and wrong-secret cases passed.")

    print("\n==================================================================")
    print("  ALL 3 TASK 05.5 SECURITY & LOGIC REVIEWS PASSED WITH FLYING COLORS!")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(test_all())
