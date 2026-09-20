"""Hardware-locked license verification system for DentalPin / DentApex Arabic.

Strict Native Architecture:
1. Native MachineGuid via Windows Registry (HKLM\\SOFTWARE\\Microsoft\\Cryptography) with KEY_WOW64_64KEY.
2. Native Volume Serial Number for C:\\ partition via ctypes.windll.kernel32.GetVolumeInformationW.
3. Zero subprocesses, Zero wmic commands.
4. MAC address completely omitted to prevent VPN/Virtual Adapter issues.
5. In-Memory caching on Startup (Lifespan) for ultra-low RAM footprint (<120MB).
6. Time-Tampering detection via cryptographically signed FirstInstall & LastRun keys.
"""

from __future__ import annotations

import ctypes
import hashlib
import hmac
import logging
import os
import winreg
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

MASTER_SECRET = b"DENTALPIN_ARABIC_MASTER_SECRET_KEY_2026_PRODUCTION"
REG_PATH = r"Software\DentalPin"
TRIAL_DURATION_DAYS = 14

# In-memory singleton state cached on Startup
_CACHED_LICENSE_STATE: dict | None = None


def _compute_hmac(data: str) -> str:
    """Compute HMAC-SHA256 signature for internal verification."""
    return hmac.new(MASTER_SECRET, data.encode("utf-8"), hashlib.sha256).hexdigest()


def get_machine_guid() -> str:
    """Read Windows MachineGuid directly from HKLM using native winreg."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        ) as key:
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(guid).strip()
    except Exception:
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ,
            ) as key:
                guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                return str(guid).strip()
        except Exception as exc:
            logger.warning("Could not read MachineGuid from winreg: %s", exc)
            return ""


def get_c_volume_serial() -> str:
    """Read Volume Serial Number for C:\\ partition directly via native ctypes."""
    try:
        vol_serial = ctypes.c_ulong()
        kernel32 = ctypes.windll.kernel32
        res = kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p("C:\\"),
            None,
            0,
            ctypes.byref(vol_serial),
            None,
            None,
            None,
            0,
        )
        if res:
            return f"{vol_serial.value:08X}"
    except Exception as exc:
        logger.warning("Could not read C: volume serial via ctypes: %s", exc)
    return ""


def get_hardware_fingerprint() -> str:
    """Extract strict native hardware fingerprint without subprocesses or MAC address."""
    guid = get_machine_guid()
    c_serial = get_c_volume_serial()

    if not guid and not c_serial:
        # Ultimate fallback: read/generate machine ID from HKCU
        fallback_id = _get_registry_str("FallbackMachineId")
        if not fallback_id:
            import uuid

            fallback_id = str(uuid.uuid4()).upper()
            _set_registry_str("FallbackMachineId", fallback_id)
        raw = f"FB:{fallback_id}"
    else:
        raw = f"{guid.upper()}:{c_serial.upper()}"

    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16].upper()
    # Format: HW-XXXX-XXXX-XXXX-XXXX (22 chars)
    return f"HW-{digest[:4]}-{digest[4:8]}-{digest[8:12]}-{digest[12:16]}"


def generate_license_key(hw_fingerprint: str, clinic_name: str) -> str:
    """Generate cryptographically signed key for a specific clinic and hardware fingerprint."""
    message = f"{hw_fingerprint.strip().upper()}:{clinic_name.strip()}".encode("utf-8")
    signature = hmac.new(MASTER_SECRET, message, hashlib.sha256).hexdigest().upper()
    return f"DP-{signature[:4]}-{signature[4:8]}-{signature[8:12]}-{signature[12:16]}"


def verify_license_key(
    license_key: str, clinic_name: str, hw_fingerprint: str | None = None
) -> bool:
    """Verify license key against clinic name and hardware fingerprint using constant-time comparison."""
    if not license_key or not clinic_name:
        return False
    current_hw = hw_fingerprint or get_hardware_fingerprint()
    expected_key = generate_license_key(current_hw, clinic_name)
    return hmac.compare_digest(license_key.strip().upper(), expected_key.strip().upper())


# --- Windows Registry Persistence Helpers ---


def _get_registry_str(name: str) -> str | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, name)
            return str(val).strip()
    except (FileNotFoundError, OSError):
        return None


def _set_registry_str(name: str, value: str) -> None:
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
    except OSError as exc:
        logger.error("Failed to write %s to registry: %s", name, exc)


def update_last_run_timestamp() -> None:
    """Update LastRun timestamp and HMAC signature in registry."""
    now_ts = str(datetime.now(UTC).timestamp())
    sig = _compute_hmac(f"last_run:{now_ts}")
    _set_registry_str("LastRun", now_ts)
    _set_registry_str("LastRunSig", sig)


def _evaluate_state_from_values(
    hw_fp: str,
    stored_key: str | None,
    stored_clinic: str | None,
    first_install_ts: float | None,
    first_install_sig: str | None,
    last_run_ts: float | None,
    last_run_sig: str | None,
    current_ts: float,
) -> dict:
    """Pure functional evaluation of license state given raw parameters."""
    # 1. Check if a valid permanent license key is present
    if stored_key and stored_clinic:
        if verify_license_key(stored_key, stored_clinic, hw_fp):
            return {
                "status": "licensed",
                "days_left": None,
                "hw_fingerprint": hw_fp,
                "clinic_name": stored_clinic,
                "is_operational_allowed": True,
                "license_key": stored_key,
                "message": "البرنامج مفعل برخصة دائمة رسمية",
            }

    # 2. Check for time tampering on LastRun
    if last_run_ts is not None and last_run_sig is not None:
        expected_sig = _compute_hmac(f"last_run:{last_run_ts}")
        if not hmac.compare_digest(last_run_sig, expected_sig):
            return {
                "status": "tampered",
                "days_left": 0,
                "hw_fingerprint": hw_fp,
                "clinic_name": stored_clinic,
                "is_operational_allowed": False,
                "license_key": None,
                "message": "تم كشف تلاعب بتوقيع السجل الزمني للنظام (Registry Signature Tampered)",
            }
        # Clock rollback check: current system time cannot be earlier than last run time (-60s tolerance)
        if current_ts < (last_run_ts - 60.0):
            return {
                "status": "tampered",
                "days_left": 0,
                "hw_fingerprint": hw_fp,
                "clinic_name": stored_clinic,
                "is_operational_allowed": False,
                "license_key": None,
                "message": "تم كشف تلاعب في ساعة النظام (Clock Rollback Detected)",
            }

    # 3. Check FirstInstall tampering
    if first_install_ts is not None and first_install_sig is not None:
        expected_fi_sig = _compute_hmac(f"first_install:{first_install_ts}")
        if not hmac.compare_digest(first_install_sig, expected_fi_sig):
            return {
                "status": "tampered",
                "days_left": 0,
                "hw_fingerprint": hw_fp,
                "clinic_name": stored_clinic,
                "is_operational_allowed": False,
                "license_key": None,
                "message": "تم كشف تلاعب بتاريخ التثبيت الأول للنظام",
            }
        if current_ts < (first_install_ts - 60.0):
            return {
                "status": "tampered",
                "days_left": 0,
                "hw_fingerprint": hw_fp,
                "clinic_name": stored_clinic,
                "is_operational_allowed": False,
                "license_key": None,
                "message": "ساعة النظام أقدم من تاريخ تثبيت البرنامج",
            }

        # Calculate 14-day trial window
        elapsed_seconds = current_ts - first_install_ts
        elapsed_days = elapsed_seconds / 86400.0

        if elapsed_days <= TRIAL_DURATION_DAYS:
            days_left = max(0, TRIAL_DURATION_DAYS - int(elapsed_days))
            return {
                "status": "trial",
                "days_left": days_left,
                "hw_fingerprint": hw_fp,
                "clinic_name": stored_clinic,
                "is_operational_allowed": True,
                "license_key": None,
                "message": f"نسخة تجريبية متبقي منها {days_left} يوم",
            }
        else:
            return {
                "status": "expired",
                "days_left": 0,
                "hw_fingerprint": hw_fp,
                "clinic_name": stored_clinic,
                "is_operational_allowed": False,
                "license_key": None,
                "message": "انتهت فترة التجربة المجانية (14 يوماً). يرجى شراء وتفعيل كود الترخيص.",
            }

    # First time run: Fresh trial initialization
    return {
        "status": "trial",
        "days_left": TRIAL_DURATION_DAYS,
        "hw_fingerprint": hw_fp,
        "clinic_name": stored_clinic,
        "is_operational_allowed": True,
        "license_key": None,
        "message": f"نسخة تجريبية جديدة (14 يوماً)",
    }


def evaluate_license_state() -> dict:
    """Evaluate current license state reading registry keys."""
    hw_fp = get_hardware_fingerprint()
    stored_key = _get_registry_str("LicenseKey")
    stored_clinic = _get_registry_str("ClinicName")

    raw_first_install = _get_registry_str("FirstInstall")
    first_install_sig = _get_registry_str("FirstInstallSig")
    first_install_ts = float(raw_first_install) if raw_first_install else None

    raw_last_run = _get_registry_str("LastRun")
    last_run_sig = _get_registry_str("LastRunSig")
    last_run_ts = float(raw_last_run) if raw_last_run else None

    now_ts = datetime.now(UTC).timestamp()

    # If first install doesn't exist, create it now
    if first_install_ts is None:
        first_install_ts = now_ts
        fi_str = str(first_install_ts)
        first_install_sig = _compute_hmac(f"first_install:{fi_str}")
        _set_registry_str("FirstInstall", fi_str)
        _set_registry_str("FirstInstallSig", first_install_sig)

    state = _evaluate_state_from_values(
        hw_fp=hw_fp,
        stored_key=stored_key,
        stored_clinic=stored_clinic,
        first_install_ts=first_install_ts,
        first_install_sig=first_install_sig,
        last_run_ts=last_run_ts,
        last_run_sig=last_run_sig,
        current_ts=now_ts,
    )

    # If state is not tampered, update LastRun now
    if state["status"] != "tampered":
        update_last_run_timestamp()

    return state


def init_license_manager() -> dict:
    """Initialize license manager at Startup lifespan. Caches state in memory."""
    global _CACHED_LICENSE_STATE
    _CACHED_LICENSE_STATE = evaluate_license_state()
    logger.info(
        "License Manager initialized: Status=%s, HW=%s, Allowed=%s",
        _CACHED_LICENSE_STATE["status"],
        _CACHED_LICENSE_STATE["hw_fingerprint"],
        _CACHED_LICENSE_STATE["is_operational_allowed"],
    )
    return _CACHED_LICENSE_STATE


def get_cached_license_state() -> dict:
    """Retrieve license state from in-memory cache with zero I/O and O(1) performance."""
    global _CACHED_LICENSE_STATE
    if _CACHED_LICENSE_STATE is None:
        return init_license_manager()
    return _CACHED_LICENSE_STATE


def activate_license(license_key: str, clinic_name: str) -> dict:
    """Validate and activate a license key, saving to registry and refreshing in-memory cache."""
    global _CACHED_LICENSE_STATE
    hw_fp = get_hardware_fingerprint()

    if not verify_license_key(license_key, clinic_name, hw_fp):
        return {
            "success": False,
            "error": "كود الترخيص غير صالح لهذه العيادة أو لهذا الجهاز.",
        }

    _set_registry_str("LicenseKey", license_key.strip().upper())
    _set_registry_str("ClinicName", clinic_name.strip())

    # Refresh in-memory cache immediately
    _CACHED_LICENSE_STATE = evaluate_license_state()

    return {
        "success": True,
        "message": "تم تفعيل رخصة البرنامج بنجاح مدى الحياة.",
        "state": _CACHED_LICENSE_STATE,
    }


def sync_db_clinic_name(db_clinic_name: str) -> None:
    """Verify that the clinic name in the database matches the licensed clinic name."""
    global _CACHED_LICENSE_STATE
    if not db_clinic_name:
        return
    state = get_cached_license_state()
    if state.get("status") == "licensed":
        stored_key = state.get("license_key")
        hw_fp = state.get("hw_fingerprint")
        if not verify_license_key(stored_key, db_clinic_name, hw_fp):
            logger.error(
                "Clinic name mismatch! DB Clinic='%s' does not match license key for HW='%s'",
                db_clinic_name,
                hw_fp,
            )
            _CACHED_LICENSE_STATE["status"] = "tampered"
            _CACHED_LICENSE_STATE["is_operational_allowed"] = False
            _CACHED_LICENSE_STATE["message"] = (
                f"تم كشف تعديل غير مصرح به على اسم العيادة في قاعدة البيانات ({db_clinic_name})، الاسم لا يتطابق مع ترخيص البرنامج."
            )

