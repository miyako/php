#!/usr/bin/env python3
"""Freeze and verify the complete, shared source/build-tool input tree."""

import argparse
import hashlib
import json
import os
from pathlib import Path


def inventory(root):
    result = {}
    for directory, directories, filenames in os.walk(root, followlinks=False):
        for name in sorted(directories + filenames):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if relative == "input-manifest.json":
                continue
            if path.is_symlink():
                result[relative] = {"link": os.readlink(path)}
            elif path.is_file():
                with path.open("rb") as source:
                    checksum = hashlib.file_digest(source, "sha256").hexdigest()
                result[relative] = {"sha256": checksum, "mode": path.stat().st_mode & 0o777}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("create", "verify"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory.resolve()
    manifest = root / "input-manifest.json"
    actual = inventory(root)
    if args.action == "create":
        manifest.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n")
    else:
        expected = json.loads(manifest.read_text())
        if actual != expected:
            differences = sorted(
                key for key in actual.keys() | expected.keys()
                if actual.get(key) != expected.get(key)
            )
            raise SystemExit(f"Source snapshot was modified: {differences[:20]}")
        print(f"Verified {len(actual)} frozen build inputs")


if __name__ == "__main__":
    main()
