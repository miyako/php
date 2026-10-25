#!/usr/bin/env python3
"""Verify Gitiles source contents and add the root directory SPC's extractor expects."""

import copy
import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tarfile
import urllib.request


def normalize(source, target):
    with tarfile.open(source) as original, target.open("wb") as output:
        with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for member in sorted(original.getmembers(), key=lambda item: item.name):
                    normalized = copy.copy(member)
                    normalized.name = "libaom/" + member.name
                    normalized.mtime = normalized.uid = normalized.gid = 0
                    normalized.uname = normalized.gname = ""
                    normalized.pax_headers = {}
                    if member.isfile():
                        with original.extractfile(member) as content:
                            archive.addfile(normalized, content)
                    else:
                        archive.addfile(normalized)


def main():
    profile = json.loads(Path(sys.argv[1]).read_text())["source_overrides"]["libaom"]
    output = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    raw = output / "libaom-upstream.tar.gz"
    with urllib.request.urlopen(profile["url"], timeout=120) as response, raw.open("wb") as target:
        shutil.copyfileobj(response, target)
    spec = importlib.util.spec_from_file_location(
        "overrides", Path(__file__).with_name("verify-overrides.py")
    )
    overrides = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(overrides)
    if overrides.tree_digest(raw) != profile["checksum"]:
        raise ValueError("Official libaom source contents do not match the pinned release")
    normalize(raw, output / profile["filename"])
    if overrides.tree_digest(output / profile["filename"], profile["tree_prefix"]) != profile["checksum"]:
        raise ValueError("Normalized libaom source contents changed")


if __name__ == "__main__":
    main()
