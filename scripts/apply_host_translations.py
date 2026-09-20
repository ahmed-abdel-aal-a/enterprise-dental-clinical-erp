#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DentalPin Arabic Localization - Central Host Locale Applier
Merges all 41 verified host section dictionaries from translations/host/
into frontend/i18n/locales/ar.json with 100% Arabic coverage.
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
TARGET_AR_PATH = os.path.join(DENTALPIN_ROOT, "frontend", "i18n", "locales", "ar.json")
EN_SOURCE_PATH = os.path.join(DENTALPIN_ROOT, "frontend", "i18n", "locales", "en.json")
HOST_TRANSLATIONS_DIR = os.path.join(BASE_DIR, "translations", "host")

def deep_merge(base, overlay):
    for k, v in overlay.items():
        if isinstance(v, dict) and k in base and isinstance(base[k], dict):
            deep_merge(base[k], v)
        else:
            base[k] = v

def get_leaves(obj, p=''):
    l = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            l.update(get_leaves(v, f'{p}.{k}' if p else k))
    else:
        l[p] = obj
    return l

def main():
    print("=" * 70)
    print("DentalPin - Applying Central Host Arabic Translations")
    print("=" * 70)

    if not os.path.exists(HOST_TRANSLATIONS_DIR):
        print(f"Error: Host translations directory not found: {HOST_TRANSLATIONS_DIR}")
        sys.exit(1)

    if not os.path.exists(EN_SOURCE_PATH):
        print(f"Error: en.json not found: {EN_SOURCE_PATH}")
        sys.exit(1)

    with open(EN_SOURCE_PATH, 'r', encoding='utf-8') as f:
        en_data = json.load(f)

    en_leaves = get_leaves(en_data)
    print(f"Target total keys in en.json: {len(en_leaves)} across {len(en_data)} sections")

    # Load existing ar.json if present
    if os.path.exists(TARGET_AR_PATH):
        with open(TARGET_AR_PATH, 'r', encoding='utf-8') as f:
            target_ar = json.load(f)
    else:
        target_ar = {}

    section_files = sorted([f for f in os.listdir(HOST_TRANSLATIONS_DIR) if f.endswith('.json')])
    print(f"Found {len(section_files)} host section translation files.")

    merged_sections = 0
    total_keys = 0

    for sfile in section_files:
        sec_name = sfile[:-5]
        spath = os.path.join(HOST_TRANSLATIONS_DIR, sfile)
        with open(spath, 'r', encoding='utf-8') as f:
            sec_dict = json.load(f)

        if sec_name in target_ar and isinstance(target_ar[sec_name], dict):
            deep_merge(target_ar[sec_name], sec_dict)
        else:
            target_ar[sec_name] = sec_dict

        leaves = get_leaves(sec_dict, sec_name)
        total_keys += len(leaves)
        merged_sections += 1
        print(f"[{merged_sections:02d}/{len(section_files)}] Merged section: {sec_name:20s} ({len(leaves)} keys)")

    # Save target ar.json
    os.makedirs(os.path.dirname(TARGET_AR_PATH), exist_ok=True)
    with open(TARGET_AR_PATH, 'w', encoding='utf-8') as f:
        json.dump(target_ar, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"Successfully merged {merged_sections} sections into {TARGET_AR_PATH}!")
    
    # Verification
    final_leaves = get_leaves(target_ar)
    missing = [k for k in en_leaves if k not in final_leaves]
    english_rem = []
    for k, v in en_leaves.items():
        if k in final_leaves:
            val = str(final_leaves[k]).strip()
            if not re.search(r'[\u0600-\u06FF]', val) and re.search(r'[a-zA-Z]{3,}', val):
                english_rem.append((k, val))

    print(f"Total keys in ar.json: {len(final_leaves)}")
    print(f"Missing keys compared to en.json: {len(missing)}")
    print(f"English strings remaining: {len(english_rem)}")
    if len(missing) == 0 and len(english_rem) == 0:
        print("VERIFICATION PASSED: 100% ARABIC PARITY ACHIEVED!")
    else:
        print("WARNING: Inconsistencies detected during verification.")
    print("=" * 70)

if __name__ == "__main__":
    main()
