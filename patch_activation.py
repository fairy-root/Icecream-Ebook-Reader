#!/usr/bin/env python3
"""
Icecream Ebook Reader v6.53 - Activation Bypass Patcher
Patches the binary to bypass online activation checks.

Findings:
  - CHECK #1 (0x0056f673): JSON status field == "success"
  - CHECK #2 (0x0056f908): Cryptographic hash validation
  - CHECK #3 (0x0056e7fb): Worker thread result check
  - UI GATE (0x00497b9d): activationFinished(bool) handler

This patcher applies 3 patches for redundancy:
  1. NOP the hash comparison JNZ (bypasses crypto check)
  2. NOP the worker thread JZ (forces success signal)
  3. NOP the UI gate JZ (always shows success dialog)
"""

import shutil
import sys
import os

try:
    import pefile
except ImportError:
    print("[!] pefile not installed. Run: pip install pefile")
    sys.exit(1)

TARGET = "icebookreader.exe"
BACKUP = "icebookreader.exe.bak"

PATCHES = [
    {
        "name": "Hash Comparison (Crypto Check)",
        "va": 0x0056f908,
        "offset_hint": 0x0016ed08,
        "original": bytes([0x85, 0xC0, 0x75, 0x36]),
        "patched":  bytes([0x85, 0xC0, 0x90, 0x90]),
        "description": "Bypasses the server hash validation. Any response with status='success' is accepted."
    },
    {
        "name": "Worker Thread Result Check",
        "va": 0x0056e7fb,
        "offset_hint": 0x0016dbfb,
        "original": bytes([0x84, 0xC0, 0x74, 0x35]),
        "patched":  bytes([0x84, 0xC0, 0x90, 0x90]),
        "description": "Forces the worker to always emit activationFinished(true)."
    },
    {
        "name": "UI Success Gate",
        "va": 0x00497b9d,
        "offset_hint": 0x00096f9d,
        "original": bytes([0x80, 0x7D, 0x08, 0x00, 0x0F, 0x84, 0x98, 0x01, 0x00, 0x00]),
        "patched":  bytes([0x80, 0x7D, 0x08, 0x00, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90]),
        "description": "Always shows the success dialog regardless of the validation result."
    }
]


def va_to_file_offset(pe, va):
    """Convert virtual address to file offset using section headers."""
    base = pe.OPTIONAL_HEADER.ImageBase
    for section in pe.sections:
        sec_va = base + section.VirtualAddress
        sec_end = sec_va + section.Misc_VirtualSize
        if sec_va <= va < sec_end:
            return section.PointerToRawData + (va - sec_va)
    raise ValueError(f"VA 0x{va:08X} not found in any section")


def main():
    if not os.path.exists(TARGET):
        print(f"[!] {TARGET} not found in current directory.")
        print(f"    Please copy icebookreader.exe here first.")
        sys.exit(1)

    # Create backup
    if not os.path.exists(BACKUP):
        shutil.copy2(TARGET, BACKUP)
        print(f"[+] Created backup: {BACKUP}")
    else:
        print(f"[*] Backup already exists: {BACKUP}")

    pe = pefile.PE(TARGET)

    with open(TARGET, "r+b") as f:
        for patch in PATCHES:
            va = patch["va"]
            try:
                offset = va_to_file_offset(pe, va)
            except ValueError as e:
                print(f"[!] Skipping {patch['name']}: {e}")
                continue

            f.seek(offset)
            current = f.read(len(patch["original"]))

            if current != patch["original"]:
                # Maybe already patched?
                if current == patch["patched"]:
                    print(f"[*] {patch['name']}: Already patched at VA 0x{va:08X}")
                    continue
                print(f"[!] {patch['name']}: Byte mismatch at VA 0x{va:08X}")
                print(f"    Expected: {patch['original'].hex()}")
                print(f"    Found:    {current.hex()}")
                print(f"    Skipping this patch.")
                continue

            f.seek(offset)
            f.write(patch["patched"])
            print(f"[+] {patch['name']}: Patched at VA 0x{va:08X} (file offset 0x{offset:08X})")
            print(f"    {patch['description']}")

    print("\n[+] Patching complete. Replace the original icebookreader.exe with the patched version.")
    print("    Original backed up as: " + BACKUP)


if __name__ == "__main__":
    main()
