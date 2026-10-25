#!/usr/bin/env python3
"""Resolve, verify, and package the official Windows x64 NTS PHP distribution."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import stat
import struct
import urllib.request
import zipfile


SCRIPTS = Path(__file__).resolve().parent
RELEASES = "https://windows.php.net/downloads/releases/"
VERSION = r"[1-9]\d*\.\d+\.\d+"


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def resolve(windows, php, requested):
    if requested == "latest":
        versions = [
            item["version"] for item in php.values()
            if re.fullmatch(VERSION, item.get("version", ""))
        ]
        version = max(versions, key=lambda value: tuple(map(int, value.split("."))))
    elif re.fullmatch(VERSION, requested):
        version = requested
    else:
        raise ValueError("Version must be 'latest' or a stable x.y.z version")
    matches = [
        item for item in windows.values() if item.get("version") == version
    ]
    if len(matches) != 1:
        raise ValueError(f"Official Windows release metadata does not publish PHP {version}; refusing an older fallback")
    variants = [name for name in matches[0] if re.fullmatch(r"nts-(?:vc|vs)\d+-x64", name)]
    if len(variants) != 1:
        raise ValueError(f"Expected exactly one official x64 NTS build for PHP {version}")
    variant = variants[0]
    archive = matches[0][variant]["zip"]
    filename = f"php-{version}-nts-Win32-{variant.split('-')[1]}-x64.zip"
    if archive["path"] != filename or not re.fullmatch(r"[0-9a-f]{64}", archive["sha256"]):
        raise ValueError("Invalid official Windows archive path or checksum")
    return {
        "version": version, "variant": variant,
        "url": RELEASES + filename, "sha256": archive["sha256"],
    }


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def download(url, checksum, output):
    if not re.fullmatch(r"[0-9a-f]{64}", checksum):
        raise ValueError("Invalid SHA-256")
    if output.is_file() and digest(output) == checksum:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    try:
        with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as target:
            shutil.copyfileobj(response, target)
        if digest(partial) != checksum:
            raise ValueError(f"Checksum mismatch for {url}")
        partial.replace(output)
    finally:
        partial.unlink(missing_ok=True)


def extract(archive, output):
    with zipfile.ZipFile(archive) as source:
        names = set()
        for member in source.infolist():
            name = member.filename.replace("\\", "/")
            path = PurePosixPath(name)
            if (not path.parts or path.is_absolute() or PureWindowsPath(name).drive or ".." in path.parts
                    or any(":" in part or part.endswith((" ", ".")) for part in path.parts)
                    or stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError(f"Unsafe archive member: {name}")
            key = "/".join(path.parts).casefold()
            if key in names:
                raise ValueError(f"Duplicate Windows archive path: {name}")
            names.add(key)
        source.extractall(output)


def verify_pe(path):
    data = path.read_bytes()
    if len(data) < 64 or data[:2] != b"MZ":
        raise ValueError(f"Not a PE executable: {path}")
    offset = struct.unpack_from("<I", data, 60)[0]
    if offset + 6 > len(data) or data[offset:offset + 4] != b"PE\0\0":
        raise ValueError(f"Invalid PE header: {path}")
    if struct.unpack_from("<H", data, offset + 4)[0] != 0x8664:
        raise ValueError(f"Not a Windows x64 executable: {path}")


def configuration(profile):
    lines = [
        "; Generated for the 4D PHP component. Paths are resolved per worker.",
        'extension_dir = "${_4D_PHP_RUNTIME}/ext"',
        'openssl.cafile = "${_4D_PHP_RUNTIME}/extras/ssl/cacert.pem"',
        'curl.cainfo = "${_4D_PHP_RUNTIME}/extras/ssl/cacert.pem"',
        'date.timezone = "UTC"',
        "error_reporting = E_ALL",
        'display_errors = "stderr"',
        "display_startup_errors = On",
        "log_errors = On",
        ";auto_prepend_file =",
    ]
    lines.extend(f"extension={name}" for name in profile["extensions"])
    return "\n".join(lines) + "\n"


def inventory(directory):
    return {
        path.relative_to(directory).as_posix(): digest(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path != directory / "runtime-manifest.json"
    }


def prepare(release, archive, output):
    if output.exists():
        raise ValueError(f"Use a fresh output directory, never overlay an older TS runtime: {output}")
    if digest(archive) != release["sha256"]:
        raise ValueError("Official PHP ZIP checksum mismatch")
    profile = json.loads((SCRIPTS / "profile.json").read_text())
    extract(archive, output)
    for name in ("php.ini", "BUILDING.md", "runtime-manifest.json", "authenticode.json",
                 "extras/ssl/cacert.pem", "extras/ssl/MPL-2.0.txt"):
        if (output / name).exists():
            raise ValueError(f"Upstream now supplies reserved packaging file {name}; review the configuration policy")
    for name in ("php.exe", "php-cgi.exe", "php8.dll"):
        verify_pe(output / name)
    if (output / "php8ts.dll").exists():
        raise ValueError("Received a thread-safe runtime instead of NTS")
    for name in profile["extensions"]:
        verify_pe(output / "ext" / f"php_{name}.dll")
    for name in ("license.txt", "readme-redist-bins.txt", "snapshot.txt"):
        if not (output / name).is_file():
            raise ValueError(f"Official redistribution notice is missing: {name}")
    download(profile["ca"]["url"], profile["ca"]["sha256"], output / "extras/ssl/cacert.pem")
    download(profile["ca_license"]["url"], profile["ca_license"]["sha256"], output / "extras/ssl/MPL-2.0.txt")
    (output / "php.ini").write_text(configuration(profile), encoding="utf-8")
    shutil.copy2(SCRIPTS / "README.md", output / "BUILDING.md")
    manifest = {
        "release": release, "architecture": "x86_64", "thread_safe": False,
        "profile": profile, "files": inventory(output),
    }
    (output / "runtime-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def verify_signatures(directory, report):
    records = json.loads(report.read_text())
    expected = {
        path.relative_to(directory).as_posix(): path
        for path in directory.rglob("*") if path.suffix.lower() in (".exe", ".dll")
    }
    actual = {}
    for record in records:
        name = record["path"]
        if name in actual or name not in expected:
            raise ValueError(f"Unexpected or duplicate Authenticode record: {name}")
        if record["status"] not in ("Valid", "NotSigned"):
            raise ValueError(f"Invalid upstream Authenticode signature: {name}: {record['status']}")
        if record["sha256"].lower() != digest(expected[name]):
            raise ValueError(f"Signature report does not match current file: {name}")
        actual[name] = record
    if set(actual) != set(expected):
        raise ValueError("Authenticode report does not cover every EXE and DLL")
    return records


def archive_runtime(directory, output, report):
    manifest_path = directory / "runtime-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if inventory(directory) != manifest["files"]:
        raise ValueError("Runtime changed after preparation")
    records = verify_signatures(directory, report)
    (directory / "authenticode.json").write_text(json.dumps(records, indent=2) + "\n")
    manifest["files"] = inventory(directory)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    output.mkdir(parents=True, exist_ok=True)
    filename = f"php-{manifest['release']['version']}-windows-x64-nts.zip"
    destination = output / filename
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                archive.write(path, "Windows/" + path.relative_to(directory).as_posix())
    (output / "SHA256SUMS").write_text(f"{digest(destination)}  {filename}\n")
    return destination


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    selection = commands.add_parser("resolve")
    selection.add_argument("--version", default="latest")
    selection.add_argument("--output", required=True, type=Path)
    preparation = commands.add_parser("prepare")
    preparation.add_argument("--release", required=True, type=Path)
    preparation.add_argument("--archive", required=True, type=Path)
    preparation.add_argument("--output", required=True, type=Path)
    packaging = commands.add_parser("archive")
    packaging.add_argument("directory", type=Path)
    packaging.add_argument("--output", required=True, type=Path)
    packaging.add_argument("--signatures", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "resolve":
        release = resolve(fetch_json(RELEASES + "releases.json"),
                          fetch_json("https://www.php.net/releases/index.php?json"), args.version)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(release, indent=2) + "\n")
        print(json.dumps(release))
    elif args.command == "prepare":
        release = json.loads(args.release.read_text())
        if not release["url"].startswith(RELEASES) or not re.fullmatch(
            r"php-\d+\.\d+\.\d+-nts-Win32-(?:vc|vs)\d+-x64\.zip",
            release["url"][len(RELEASES):],
        ):
            raise ValueError("Archive is not an official x64 NTS release URL")
        download(release["url"], release["sha256"], args.archive)
        prepare(release, args.archive, args.output)
    else:
        print(archive_runtime(args.directory.resolve(), args.output, args.signatures))


if __name__ == "__main__":
    main()
