"""Developer Key Generator CLI for DentApex Arabic Edition.

Used exclusively by the software developer/distributor to generate cryptographically
signed, hardware-locked lifetime license keys for dental clinics.
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure backend app is discoverable
BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "dentalpin-main", "backend")
)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.license import generate_license_key, get_hardware_fingerprint, verify_license_key


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DentApex Arabic - Commercial License Key Generator"
    )
    parser.add_argument(
        "--hw",
        type=str,
        default=None,
        help="Hardware Fingerprint (e.g. HW-XXXX-XXXX-XXXX-XXXX). If omitted, detects current machine.",
    )
    parser.add_argument(
        "--clinic",
        type=str,
        default=None,
        help="Official Clinic Name (e.g. 'عيادة النور لطب الأسنان')",
    )

    args = parser.parse_args()

    hw_id = args.hw
    clinic_name = args.clinic

    # Interactive mode if arguments are missing
    if not hw_id or not clinic_name:
        print("=" * 65)
        print("🌟 أداة توليد تراخيص DentApex الرسمية (DentApex Key Generator)")
        print("=" * 65)

        if not hw_id:
            current_local_hw = get_hardware_fingerprint()
            prompt = f"أدخل بصمة عتاد الجهاز [اضغط Enter لاستخدام عتاد هذا الجهاز: {current_local_hw}]: "
            user_hw = input(prompt).strip()
            hw_id = user_hw if user_hw else current_local_hw

        if not clinic_name:
            while not clinic_name:
                clinic_name = input("أدخل اسم العيادة بالكامل (كما يظهر في البرنامج): ").strip()
                if not clinic_name:
                    print("⚠️ اسم العيادة مطلوب ولا يمكن تركه فارغاً!")

    # Format & Clean inputs
    hw_id = hw_id.strip().upper()
    clinic_name = clinic_name.strip()

    # Generate cryptographically signed license key
    key = generate_license_key(hw_id, clinic_name)

    # Double check cryptographic validity
    is_valid = verify_license_key(key, clinic_name, hw_id)
    if not is_valid:
        print("\n❌ فشل التحقق الرياضي الداخلي من المفتاح! يرجى مراجعة المدخلات.")
        sys.exit(1)

    print("\n" + "=" * 65)
    print("✅ تم توليد رخصة البرنامج الدائمة بنجاح:")
    print("=" * 65)
    print(f"🏥 اسم العيادة  : {clinic_name}")
    print(f"💻 بصمة العتاد   : {hw_id}")
    print(f"🔑 كود الترخيص  : {key}")
    print("=" * 65)
    print("📌 أرسل كود الترخيص للطبيب مع التنبيه بضرورة كتابة اسم العيادة بنفس الحروف.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
