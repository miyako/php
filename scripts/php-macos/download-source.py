#!/usr/bin/env python3
"""Fetch only the resolved official archive and verify it before use."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request


def download(release, output):
    version = release["version"]
    checksum = release["sha256"]
    if not re.fullmatch(r"[1-9]\d*\.\d+\.\d+", version):
        raise ValueError("Invalid PHP release version")
    if not re.fullmatch(r"[0-9a-f]{64}", checksum):
        raise ValueError("Invalid PHP source checksum")
    expected_url = f"https://www.php.net/distributions/php-{version}.tar.xz"
    if release["url"] != expected_url:
        raise ValueError("Source URL is not the official release archive")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(expected_url, timeout=120) as response, partial.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                target.write(chunk)
        if digest.hexdigest() != checksum:
            raise ValueError(f"PHP source checksum mismatch: expected {checksum}, got {digest.hexdigest()}")
        partial.replace(output)
    finally:
        partial.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    download(json.loads(args.release.read_text()), args.output)


if __name__ == "__main__":
    main()
