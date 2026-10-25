#!/usr/bin/env python3
"""Verify pinned dependency replacements before freezing or building inputs."""

import hashlib
import json
from pathlib import Path
import sys
import tarfile


def tree_digest(path, prefix=""):
    # Gitiles regenerates tar headers/compression; pin the actual source tree instead.
    contents = {}
    with tarfile.open(path) as archive:
        for member in archive:
            if member.isdir():
                continue
            if not member.name.startswith(prefix):
                raise ValueError(f"Source archive member lacks expected prefix: {member.name}")
            name = member.name[len(prefix):]
            if name in contents:
                raise ValueError(f"Duplicate archive member: {name}")
            if member.issym():
                contents[name] = {"mode": member.mode & 0o7777, "link": member.linkname}
            elif member.isfile():
                with archive.extractfile(member) as source:
                    contents[name] = {
                        "mode": member.mode & 0o7777,
                        "sha256": hashlib.file_digest(source, "sha256").hexdigest(),
                    }
            else:
                raise ValueError(f"Unsupported source archive member: {member.name}")
    canonical = json.dumps(contents, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def verify(root):
    profile = json.loads((root / "runtime-profile.json").read_text())
    for name, source in profile["source_overrides"].items():
        path = root / "downloads" / source["filename"]
        if source["algorithm"] == "tar-tree-sha256":
            actual = tree_digest(path, source.get("tree_prefix", ""))
        else:
            with path.open("rb") as archive:
                actual = hashlib.file_digest(archive, source["algorithm"]).hexdigest()
        if actual != source["checksum"]:
            raise ValueError(f"{name} checksum mismatch: expected {source['checksum']}, got {actual}")
        print(f"Verified pinned {name}: {actual}")


if __name__ == "__main__":
    verify(Path(sys.argv[1]))
