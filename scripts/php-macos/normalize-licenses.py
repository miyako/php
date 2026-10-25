#!/usr/bin/env python3
"""Require a notice for every source artifact and remove nonportable dump timestamps."""

import json
import os
from pathlib import Path
import shutil
import sys


def normalize(root):
    cache = json.loads((root / "downloads/.cache.json").read_text())
    expected = {name for name, entry in cache.items() if entry.get("source")}
    directory = root / "buildroot/license"
    summary_path = directory / "SUMMARY.json"
    summary = json.loads(summary_path.read_text())
    artifacts = summary["artifacts"]
    if not expected or expected != set(artifacts):
        raise ValueError(f"License/source inventory mismatch: {sorted(expected ^ set(artifacts))}")
    for name, metadata in artifacts.items():
        notice = directory / f"{name}_LICENSE.txt"
        if not notice.is_file() or not notice.read_bytes().strip():
            raise ValueError(f"Missing or empty license notice for {name}")
        metadata.pop("dumped-at", None)
        source = root / "source" / name
        if not source.is_dir():
            raise ValueError(f"Missing extracted source for license collection: {name}")
        for current, directories, filenames in os.walk(source, followlinks=False):
            directories[:] = sorted(
                item for item in directories
                if item not in (".git", ".deps", ".libs", "CMakeFiles", "builddir")
            )
            for filename in sorted(filenames):
                path = Path(current) / filename
                if path.is_symlink() or not filename.upper().startswith(
                    ("LICENSE", "LICENCE", "COPYING", "COPYRIGHT", "NOTICE", "PATENTS")
                ):
                    continue
                if path.suffix.lower() in (".c", ".h", ".cpp", ".py", ".js", ".php", ".sh"):
                    continue
                destination = directory / "upstream" / name / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
    if summary["summary"]["total-artifacts"] != len(expected):
        raise ValueError("License summary count does not match source inventory")
    summary["summary"].pop("last-updated", None)
    summary["summary"]["license-types"] = {
        name: sorted(members) for name, members in summary["summary"]["license-types"].items()
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    normalize(Path(sys.argv[1]))
