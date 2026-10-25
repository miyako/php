#!/usr/bin/env python3
"""Resolve an official stable PHP release once for both architecture builds."""

import argparse
import json
from pathlib import Path
import re
import urllib.request


def resolve(metadata, requested):
    version = metadata["version"]
    if not re.fullmatch(r"[1-9]\d*\.\d+\.\d+", version):
        raise ValueError(f"Not a stable PHP release: {version!r}")
    if requested != "latest" and requested != version:
        raise ValueError(f"Requested {requested}, received {version}")
    filename = f"php-{version}.tar.xz"
    source = next(item for item in metadata["source"] if item["filename"] == filename)
    checksum = source["sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", checksum):
        raise ValueError("Official release metadata has no valid SHA-256")
    return {
        "version": version,
        "url": f"https://www.php.net/distributions/{filename}",
        "sha256": checksum,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("version", nargs="?", default="latest")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.version != "latest" and not re.fullmatch(r"[1-9]\d*\.\d+\.\d+", args.version):
        parser.error("version must be 'latest' or a stable PHP version (x.y.z)")
    url = "https://www.php.net/releases/index.php?json"
    if args.version != "latest":
        url += f"&version={args.version}"
    with urllib.request.urlopen(url, timeout=60) as response:
        metadata = json.load(response)
    if args.version == "latest":
        candidates = [
            item for item in metadata.values()
            if re.fullmatch(r"[1-9]\d*\.\d+\.\d+", item.get("version", ""))
        ]
        metadata = max(candidates, key=lambda item: tuple(map(int, item["version"].split("."))))
    release = resolve(metadata, args.version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(release, indent=2) + "\n")
    print(json.dumps(release))


if __name__ == "__main__":
    main()
