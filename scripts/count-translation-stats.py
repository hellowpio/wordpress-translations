#!/usr/bin/env python3
"""
Translation Statistics Counter for WordPress PO Files

This script analyzes all .po files in the repository and provides
detailed statistics about the translations including character counts,
entry counts, and translation completion rates.

Usage:
    python3 scripts/count-translation-stats.py
"""

import re
import glob
import os
import sys

def count_translation_stats():
    """Count and analyze translation statistics from all PO files."""

    # Change to script's parent directory (repository root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)

    total_msgid_chars = 0
    total_msgstr_chars = 0
    total_entries = 0
    total_translated = 0

    print("🔍 Scanning all PO files for character count...\n")

    po_files = glob.glob('plugins/**/*.po', recursive=True) + glob.glob('themes/**/*.po', recursive=True)

    for po_file in po_files:
        try:
            with open(po_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            current_msgid = []
            current_msgstr = []
            in_msgid = False
            in_msgstr = False

            for line in lines:
                line = line.strip()

                # Start of msgid
                if line.startswith('msgid '):
                    if current_msgid and current_msgstr:
                        # Process previous entry
                        msgid_text = ''.join(current_msgid)
                        msgstr_text = ''.join(current_msgstr)

                        if msgid_text:  # Skip empty msgid
                            total_msgid_chars += len(msgid_text)
                            total_entries += 1

                            if msgstr_text:
                                total_msgstr_chars += len(msgstr_text)
                                total_translated += 1

                    # Start new entry
                    current_msgid = [line[7:-1] if line.endswith('"') and line[6:].startswith('"') else '']
                    current_msgstr = []
                    in_msgid = True
                    in_msgstr = False

                # Start of msgstr
                elif line.startswith('msgstr '):
                    current_msgstr = [line[8:-1] if line.endswith('"') and line[7:].startswith('"') else '']
                    in_msgid = False
                    in_msgstr = True

                # Continuation line
                elif line.startswith('"') and line.endswith('"'):
                    text = line[1:-1]
                    if in_msgid:
                        current_msgid.append(text)
                    elif in_msgstr:
                        current_msgstr.append(text)
                else:
                    in_msgid = False
                    in_msgstr = False

            # Process last entry
            if current_msgid and current_msgstr:
                msgid_text = ''.join(current_msgid)
                msgstr_text = ''.join(current_msgstr)

                if msgid_text:
                    total_msgid_chars += len(msgid_text)
                    total_entries += 1

                    if msgstr_text:
                        total_msgstr_chars += len(msgstr_text)
                        total_translated += 1

        except Exception as e:
            print(f"Error processing {po_file}: {e}")

    # Calculate statistics
    translation_rate = (total_translated / total_entries * 100) if total_entries > 0 else 0

    # Display results
    print(f"📊 Statistics:")
    print(f"   Total PO files: {len(po_files):,}")
    print(f"   Total translation entries: {total_entries:,}")
    print(f"   Total translated entries: {total_translated:,} ({translation_rate:.1f}%)")
    print(f"\n📝 Character count:")
    print(f"   English (msgid): {total_msgid_chars:,} characters")
    print(f"   Hungarian (msgstr): {total_msgstr_chars:,} characters")

    if total_msgid_chars > 0:
        diff = total_msgstr_chars - total_msgid_chars
        diff_percent = (total_msgstr_chars / total_msgid_chars * 100) - 100
        print(f"\n📈 Difference:")
        print(f"   {diff:+,} characters ({diff_percent:+.2f}%)")

if __name__ == '__main__':
    count_translation_stats()
