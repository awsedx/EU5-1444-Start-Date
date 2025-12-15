#!/usr/bin/env python3
"""
Remove country tags listed in an error log from the international organizations file.

Usage:
  python3 scripts/remove_international_org_entries.py --log /path/to/error.log
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import sys
from typing import Set, Tuple, Optional


def extract_tags_from_log(path: str) -> Set[str]:
    tags = set()
    # Look for lines that contain "CountryDoesNotExist" and extract the tag
    # Example:
    # [22:48:55][international_organization.cpp:1472]: GRF is in a hre but will auto-leave on day 1 (CountryDoesNotExist)
    pattern = re.compile(r"\]:\s*([A-Z]{2,3})\b.*CountryDoesNotExist")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "CountryDoesNotExist" not in line:
                    continue
                m = pattern.search(line)
                if m:
                    tags.add(m.group(1))
    except FileNotFoundError:
        print(f"Error: log file not found: {path}", file=sys.stderr)
        sys.exit(2)
    return tags


def extract_dependency_tags_from_log(path: str) -> Set[str]:
    """Extract tags from lines like:
    [..]: Dependency with non-existent subject (CWM)
    [..]: Dependency with non-existent overlord (NZH)
    """
    tags = set()
    pattern = re.compile(r"Dependency with non-existent (?:subject|overlord)[^\(]*\(([A-Z]{2,3})\)")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "Dependency with non-existent" not in line:
                    continue
                m = pattern.search(line)
                if m:
                    tags.add(m.group(1))
    except FileNotFoundError:
        print(f"Error: log file not found: {path}", file=sys.stderr)
        sys.exit(2)
    return tags


def count_tag_occurrences_in_file(path: str, tags: Set[str]) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
    except FileNotFoundError:
        return 0
    return sum(data.count(tag) for tag in tags)


def count_lines_with_tags_in_file(path: str, tags: Set[str]) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return 0
    cnt = 0
    for line in lines:
        for tag in tags:
            if re.search(r"\b" + re.escape(tag) + r"\b", line):
                cnt += 1
                break
    return cnt


def remove_lines_containing_tags(file_path: str, tags: Set[str], backup: bool = True) -> Tuple[int, Optional[str]]:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Warning: file not found: {file_path}", file=sys.stderr)
        return 0, None

    keep = []
    removed = 0
    for line in lines:
        if any(re.search(r"\b" + re.escape(tag) + r"\b", line) for tag in tags):
            removed += 1
            continue
        keep.append(line)

    if removed == 0:
        return 0, None

    if backup:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        bak_path = f"{file_path}.bak.{timestamp}"
        shutil.copy2(file_path, bak_path)
    else:
        bak_path = None

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(keep)

    return removed, bak_path


def remove_tags_from_file(org_path: str, tags: Set[str], backup: bool = True) -> Tuple[int, Optional[str]]:
    if not tags:
        return 0, None

    try:
        with open(org_path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: organizations file not found: {org_path}", file=sys.stderr)
        sys.exit(3)

    original = data

    # Remove whole-word occurrences of each tag, leaving surrounding whitespace/newlines intact.
    for tag in sorted(tags, key=lambda s: (-len(s), s)):
        data = re.sub(r"\b" + re.escape(tag) + r"\b", "", data)

    if backup:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        bak_path = f"{org_path}.bak.{timestamp}"
        shutil.copy2(org_path, bak_path)
    else:
        bak_path = None

    with open(org_path, "w", encoding="utf-8") as f:
        f.write(data)

    removed_count = sum(original.count(tag) - data.count(tag) for tag in tags)
    return removed_count, bak_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove tags found in an error log from the international organizations file.")
    parser.add_argument("--log", "-l", required=True, help="Path to the error log file")
    parser.add_argument("--dry-run", action="store_true", help="Don't modify the organizations file; just print the tags that would be removed")
    parser.add_argument("--no-backup", action="store_true", help="Do not create a backup before writing")
    args = parser.parse_args()

    log_path = args.log

    # Enforce repository-default organizations file. Do not allow overriding.
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    org_path = os.path.join(repo_root, "main_menu", "setup", "start", "15_international_organizations.txt")

    org_path = os.path.expanduser(org_path)

    tags = extract_tags_from_log(log_path)
    dep_tags = extract_dependency_tags_from_log(log_path)
    if not tags and not dep_tags:
        print("No tags found in log matching pattern. Nothing to do.")
        return

    print(f"Found {len(tags)} unique organization-tag(s) in log:")
    if tags:
        print(", ".join(sorted(tags)))
    print(f"Found {len(dep_tags)} unique dependency-tag(s) in log:")
    if dep_tags:
        print(", ".join(sorted(dep_tags)))

    if args.dry_run:
        print("Dry run: no file modifications will be made.")
        return

    # Dry run: compute counts but don't write
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    diplomacy_path = os.path.join(repo_root, "main_menu", "setup", "start", "12_diplomacy.txt")

    if args.dry_run:
        org_occurrences = count_tag_occurrences_in_file(org_path, tags)
        dip_lines = count_lines_with_tags_in_file(diplomacy_path, dep_tags)
        print(f"Dry run: would remove {org_occurrences} tag occurrences from '{org_path}'.")
        print(f"Dry run: would remove {dip_lines} lines from '{diplomacy_path}'.")
        print("Dry run: no file modifications will be made.")
        return

    removed_count, bak = remove_tags_from_file(org_path, tags, backup=not args.no_backup)
    print(f"Removed {removed_count} total tag occurrences from '{org_path}'.")
    if bak:
        print(f"Backup created: {bak}")

    dip_removed, dip_bak = remove_lines_containing_tags(diplomacy_path, dep_tags, backup=not args.no_backup)
    print(f"Removed {dip_removed} lines from '{diplomacy_path}'.")
    if dip_bak:
        print(f"Backup created: {dip_bak}")


if __name__ == "__main__":
    main()
