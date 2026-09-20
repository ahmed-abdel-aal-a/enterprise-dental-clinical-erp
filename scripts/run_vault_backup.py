"""DentApex Vault Backup Script - Generates local encrypted snapshot and syncs to R2."""

import asyncio
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add backend directory to sys.path and load .env
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
from app.core.r2_vault import VaultSnapshotService, encrypt_payload
from app.core.auth.models import Clinic
import httpx


async def run_backup():
    print("==================================================================")
    print("       DentApex R2 Vault - Automated Encrypted Snapshot           ")
    print("==================================================================")

    # Register all module models so relationships resolve
    register_discovered()

    data_vault_dir = Path(__file__).resolve().parent.parent / "data" / "vault"
    data_vault_dir.mkdir(parents=True, exist_ok=True)

    async with async_session_maker() as session:
        clinics_res = await session.execute(select(Clinic))
        clinics = clinics_res.scalars().all()

        if not clinics:
            print("[!] No active clinics found in database.")
            return

        for clinic in clinics:
            print(f"[*] Processing snapshot for Clinic: {clinic.name} ({clinic.id})")
            snapshot = await VaultSnapshotService.build_snapshot(session, clinic.id)
            print(f"    - Patients indexed:    {len(snapshot['patients'])}")
            print(f"    - Appointments cached: {len(snapshot['appointments'])}")
            print(f"    - Catalog items:       {len(snapshot['catalog'])}")

            secret = settings.SECRET_KEY
            encrypted_blob = encrypt_payload(snapshot, secret)
            print(f"    - Encrypted payload size: {len(encrypted_blob)} bytes (AES-256-GCM)")

            # Save local encrypted copy
            local_file = data_vault_dir / f"dentapex_vault_{clinic.id}.enc"
            with open(local_file, "wb") as f:
                f.write(encrypted_blob)
            print(f"    [OK] Local encrypted snapshot saved to: {local_file.name}")

            # Optional remote upload to Edge Worker if configured
            edge_url = getattr(settings, "EDGE_WORKER_URL", None) or os.environ.get("EDGE_WORKER_URL")
            vault_key = getattr(settings, "CLINIC_VAULT_KEY", None) or os.environ.get("CLINIC_VAULT_KEY")

            if edge_url and vault_key:
                print(f"[*] Syncing to Cloudflare Edge Worker: {edge_url} ...")
                try:
                    target_endpoint = f"{edge_url.rstrip('/')}/api/edge/vault/snapshot?clinic_id={clinic.id}"
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.put(
                            target_endpoint,
                            content=encrypted_blob,
                            headers={"X-Clinic-Vault-Key": vault_key},
                        )
                    if resp.status_code == 200:
                        print(f"    [SUCCESS] Snapshot uploaded to Cloudflare R2 Vault!")
                    else:
                        print(f"    [!] Remote upload returned status {resp.status_code}: {resp.text}")
                except Exception as e:
                    print(f"    [!] Remote sync failed: {e}")
            else:
                print("    [*] Remote Edge Worker sync skipped (EDGE_WORKER_URL not configured).")

    print("==================================================================")
    print("  [SUCCESS] DentApex Vault snapshot process completed.")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(run_backup())
