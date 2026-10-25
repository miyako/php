#!/usr/bin/env python3
"""Offline tests for Windows release selection, integrity, configuration, and packaging."""

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile


spec = importlib.util.spec_from_file_location("windows_package", Path(__file__).with_name("package.py"))
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


def pe(machine=0x8664):
    data = bytearray(160)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 60, 128)
    data[128:132] = b"PE\0\0"
    struct.pack_into("<H", data, 132, machine)
    return bytes(data)


class ReleaseTests(unittest.TestCase):
    def metadata(self):
        return {
            "8.5": {"version": "8.5.12", "nts-vs17-x64": {"zip": {
                "path": "php-8.5.12-nts-Win32-vs17-x64.zip", "sha256": "a" * 64,
            }}},
        }, {"8": {"version": "8.5.12"}, "7": {"version": "7.4.33"}}

    def test_latest_and_exact_release_select_only_nts_x64(self):
        windows, php = self.metadata()
        for requested in ("latest", "8.5.12"):
            result = package.resolve(windows, php, requested)
            self.assertEqual(result["version"], "8.5.12")
            self.assertEqual(result["variant"], "nts-vs17-x64")
            self.assertEqual(result["sha256"], "a" * 64)

    def test_windows_lag_does_not_silently_select_an_older_php(self):
        windows, php = self.metadata()
        php["8"]["version"] = "8.5.13"
        with self.assertRaisesRegex(ValueError, "refusing an older fallback"):
            package.resolve(windows, php, "latest")

    def test_ts_x86_prereleases_and_bad_hashes_are_rejected(self):
        for bad_variant in ("ts-vs17-x64", "nts-vs17-x86"):
            windows, php = self.metadata()
            windows["8.5"][bad_variant] = windows["8.5"].pop("nts-vs17-x64")
            with self.assertRaisesRegex(ValueError, "x64 NTS"):
                package.resolve(windows, php, "latest")
        windows, php = self.metadata()
        windows["8.5"]["nts-vs17-x64"]["zip"]["sha256"] = ""
        with self.assertRaises(ValueError):
            package.resolve(windows, php, "latest")
        with self.assertRaises(ValueError):
            package.resolve(windows, php, "8.6.0RC1")

    def test_archive_path_is_not_taken_on_trust(self):
        windows, php = self.metadata()
        windows["8.5"]["nts-vs17-x64"]["zip"]["path"] = "../php.exe"
        with self.assertRaisesRegex(ValueError, "archive path"):
            package.resolve(windows, php, "latest")


class ArchiveTests(unittest.TestCase):
    def test_windows_paths_cannot_escape_or_alias(self):
        for name in ("../escape", "..\\escape", "C:/escape", "/escape", "dir/file:stream", "dir./file"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                archive = root / "input.zip"
                with zipfile.ZipFile(archive, "w") as target:
                    target.writestr(name, b"data")
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    package.extract(archive, root / "output")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "input.zip"
            with zipfile.ZipFile(archive, "w") as target:
                target.writestr("EXT/a.dll", b"one")
                target.writestr("ext/./a.dll", b"two")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                package.extract(archive, root / "output")

    def test_archive_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "input.zip"
            with zipfile.ZipFile(archive, "w") as target:
                member = zipfile.ZipInfo("link")
                member.create_system = 3
                member.external_attr = (stat.S_IFLNK | 0o777) << 16
                target.writestr(member, "../outside")
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                package.extract(archive, root / "output")

    def test_wrong_pe_architecture_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "php.exe"
            executable.write_bytes(pe())
            package.verify_pe(executable)
            executable.write_bytes(pe(0x14C))
            with self.assertRaisesRegex(ValueError, "x64"):
                package.verify_pe(executable)

    def test_download_checksum_failure_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "input.zip"
            output.write_bytes(b"old")
            with patch.object(package.urllib.request, "urlopen", return_value=io.BytesIO(b"bad")):
                with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
                    package.download("https://example.invalid/input.zip", "a" * 64, output)
            self.assertEqual(output.read_bytes(), b"old")
            self.assertFalse(output.with_suffix(".zip.partial").exists())


class PackagingTests(unittest.TestCase):
    def prepare(self, root):
        config = root / "scripts"
        config.mkdir()
        trust = b"test trust data"
        profile = {
            "extensions": ["mbstring"], "required_modules": ["Core", "mbstring"],
            "ca": {"url": "https://example.invalid/ca", "sha256": hashlib.sha256(trust).hexdigest()},
            "ca_license": {"url": "https://example.invalid/license", "sha256": hashlib.sha256(trust).hexdigest()},
        }
        (config / "profile.json").write_text(json.dumps(profile))
        (config / "README.md").write_text("Runtime documentation\n")
        archive = root / "input.zip"
        with zipfile.ZipFile(archive, "w") as target:
            for name in ("php.exe", "php-cgi.exe", "php8.dll", "ext/php_mbstring.dll"):
                target.writestr(name, pe())
            for name in ("license.txt", "readme-redist-bins.txt", "snapshot.txt"):
                target.writestr(name, "Official redistribution notice\n")
        release = {"version": "8.5.12", "sha256": package.digest(archive)}
        runtime = root / "Windows"
        with patch.object(package, "SCRIPTS", config), patch.object(
            package.urllib.request, "urlopen", side_effect=lambda *args, **kwargs: io.BytesIO(trust)
        ):
            package.prepare(release, archive, runtime)
        return runtime, release, archive

    def report(self, root, runtime):
        records = [
            {"path": path.relative_to(runtime).as_posix(), "status": "NotSigned",
             "sha256": package.digest(path), "signer_thumbprint": None}
            for path in runtime.rglob("*") if path.suffix in (".exe", ".dll")
        ]
        path = root / "signatures.json"
        path.write_text(json.dumps(records))
        return path

    def test_payload_config_and_final_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime, release, upstream = self.prepare(root)
            with zipfile.ZipFile(upstream) as source:
                for name in source.namelist():
                    self.assertEqual((runtime / name).read_bytes(), source.read(name))
            ini = (runtime / "php.ini").read_text()
            self.assertIn('extension_dir = "${_4D_PHP_RUNTIME}/ext"', ini)
            self.assertIn(";auto_prepend_file =", ini)
            self.assertIn("extension=mbstring", ini)
            self.assertNotIn(str(root), ini)
            result = package.archive_runtime(runtime, root / "distribution", self.report(root, runtime))
            with zipfile.ZipFile(result) as archive:
                self.assertIn("Windows/authenticode.json", archive.namelist())
                self.assertIn("Windows/ext/php_mbstring.dll", archive.namelist())
                manifest = json.loads(archive.read("Windows/runtime-manifest.json"))
                self.assertEqual(manifest["release"], release)
                self.assertFalse(manifest["thread_safe"])
            self.assertIn(package.digest(result), (result.parent / "SHA256SUMS").read_text())

    def test_existing_output_and_wrong_archive_hash_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime, release, archive = self.prepare(root)
            with self.assertRaisesRegex(ValueError, "never overlay"):
                package.prepare(release, archive, runtime)
            with self.assertRaisesRegex(ValueError, "ZIP checksum"):
                package.prepare({**release, "sha256": "0" * 64}, archive, root / "new")

    def test_modified_payload_is_not_packaged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime, _, _ = self.prepare(root)
            report = self.report(root, runtime)
            (runtime / "php.exe").write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "changed after preparation"):
                package.archive_runtime(runtime, root / "distribution", report)

    def test_invalid_incomplete_or_stale_signature_reports_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime, _, _ = self.prepare(root)
            report = self.report(root, runtime)
            original = json.loads(report.read_text())
            for records in (
                original[:-1],
                [{**original[0], "status": "HashMismatch"}] + original[1:],
                [{**original[0], "sha256": "0" * 64}] + original[1:],
            ):
                report.write_text(json.dumps(records))
                with self.assertRaises(ValueError):
                    package.verify_signatures(runtime, report)


if __name__ == "__main__":
    unittest.main()
