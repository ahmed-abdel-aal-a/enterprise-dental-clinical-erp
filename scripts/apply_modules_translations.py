#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DentalPin Arabic Localization - Module Translations Applier
Applies the verified 21-module Arabic dictionaries into each module's
backend/app/modules/<module_name>/frontend/i18n/locales/
and updates nuxt.config.ts to register the 'ar' locale.
"""

import os
import sys
import json
import re

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DENTALPIN_ROOT = os.path.join(PROJECT_ROOT, "dentalpin-main")
MODULES_DIR = os.path.join(DENTALPIN_ROOT, "backend", "app", "modules")
TRANSLATIONS_DIR = os.path.join(BASE_DIR, "translations", "modules")

MODULE_MAPPING = {
    "accounting_export.json": "accounting_export",
    "activity_journal.json": "activity_journal",
    "clinical_notes.json": "clinical_notes",
    "contacts.json": "contacts",
    "expenses.json": "expenses",
    "india_gst.json": "india_gst",
    "inventory.json": "inventory",
    "lab_orders.json": "lab_orders",
    "medical_reference.json": "medical_reference",
    "medication_catalog.json": "medication_catalog",
    "migration_import.json": "migration_import",
    "notifications.json": "notifications",
    "patient_relationships.json": "patient_relationships",
    "payments.json": "payments",
    "periodontogram.json": "periodontogram",
    "recalls.json": "recalls",
    "schedules.json": "schedules",
    "staff_tasks.json": "staff_tasks",
    "treatment_consumables.json": "treatment_consumables",
    "verifactu.json": "verifactu",
    "whatsapp_kapso.json": "whatsapp_kapso",
}

def update_nuxt_config(config_path, locale_filename):
    """Ensure Arabic locale entry is in nuxt.config.ts i18n locales list."""
    if not os.path.exists(config_path):
        return False, "Config file not found"

    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if 'ar' locale is already registered
    if re.search(r"code:\s*['\"]ar['\"]", content):
        return True, "Already configured"

    # Pattern to find locales array in i18n
    # e.g.: locales: [{ code: 'en', file: 'en.json' }, ...]
    locales_match = re.search(r"(locales:\s*\[)([\s\S]*?)(\])", content)
    if not locales_match:
        return False, "i18n locales block not found in nuxt.config.ts"

    prefix = locales_match.group(1)
    existing_entries = locales_match.group(2)
    suffix = locales_match.group(3)

    ar_entry = f"{{ code: 'ar', file: '{locale_filename}' }}"
    
    if existing_entries.strip():
        new_entries = existing_entries.rstrip() + f",\n      {ar_entry}\n    "
    else:
        new_entries = f"\n      {ar_entry}\n    "

    new_content = content[:locales_match.start()] + prefix + new_entries + suffix + content[locales_match.end():]

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True, "Registered successfully"

def main():
    print("=" * 70)
    print("DentalPin - Applying Translations for all 21 Modules")
    print("=" * 70)

    if not os.path.exists(TRANSLATIONS_DIR):
        print(f"Error: Translations directory not found: {TRANSLATIONS_DIR}")
        sys.exit(1)

    if not os.path.exists(MODULES_DIR):
        print(f"Error: Modules directory not found: {MODULES_DIR}")
        sys.exit(1)

    applied_count = 0
    total_keys = 0

    for json_file, mod_name in sorted(MODULE_MAPPING.items()):
        src_path = os.path.join(TRANSLATIONS_DIR, json_file)
        if not os.path.exists(src_path):
            print(f"[!] Warning: Missing source file: {json_file}")
            continue

        with open(src_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)

        mod_frontend = os.path.join(MODULES_DIR, mod_name, "frontend")
        locales_dir = os.path.join(mod_frontend, "i18n", "locales")
        os.makedirs(locales_dir, exist_ok=True)

        # Target locale filename
        if mod_name == "notifications":
            locale_file = "notifications-ar.json"
        else:
            locale_file = "ar.json"

        target_path = os.path.join(locales_dir, locale_file)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)

        # Update nuxt.config.ts
        nuxt_config_path = os.path.join(mod_frontend, "nuxt.config.ts")
        configured, msg = update_nuxt_config(nuxt_config_path, locale_file)

        # Count keys
        def count_leaves(d):
            c = 0
            for k, v in d.items():
                if isinstance(v, dict):
                    c += count_leaves(v)
                else:
                    c += 1
            return c

        k_count = count_leaves(translations)
        total_keys += k_count
        applied_count += 1
        print(f"[{applied_count:02d}/21] {mod_name:25s} -> {locale_file} ({k_count} keys) | nuxt.config.ts: {msg}")

    print("\n" + "=" * 70)
    print(f"Successfully applied Arabic translations to {applied_count}/21 modules!")
    print(f"Total module keys translated: {total_keys}")
    print("=" * 70)

if __name__ == "__main__":
    main()
