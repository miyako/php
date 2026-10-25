#!/usr/bin/env python3
"""Tests for release selection and the dependency-free FastCGI client."""

import importlib.util
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import struct
import subprocess
import tempfile
import tarfile
import threading
import unittest
from unittest.mock import patch


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load("release", "resolve-release.py")
smoke = load("smoke", "smoke-test.py")
source = load("source", "download-source.py")
snapshot = load("snapshot", "snapshot.py")
overrides = load("overrides", "verify-overrides.py")
libaom = load("libaom", "normalize-libaom.py")
licenses = load("licenses", "normalize-licenses.py")


class ReleaseTests(unittest.TestCase):
    def metadata(self, version="8.5.12", checksum="a" * 64):
        return {
            "version": version,
            "source": [{"filename": f"php-{version}.tar.xz", "sha256": checksum}],
        }

    def test_latest_and_explicit_release(self):
        for requested in ("latest", "8.5.12"):
            result = release.resolve(self.metadata(), requested)
            self.assertEqual(result["version"], "8.5.12")
            self.assertEqual(result["url"], "https://www.php.net/distributions/php-8.5.12.tar.xz")
            self.assertEqual(result["sha256"], "a" * 64)

    def test_rejects_prerelease(self):
        with self.assertRaises(ValueError):
            release.resolve(self.metadata("8.6.0RC1"), "latest")

    def test_rejects_mismatched_release(self):
        with self.assertRaises(ValueError):
            release.resolve(self.metadata(), "8.5.11")

    def test_rejects_missing_checksum(self):
        with self.assertRaises(ValueError):
            release.resolve(self.metadata(checksum=""), "latest")


class FastCGITests(unittest.TestCase):
    def test_name_value_lengths_precede_content(self):
        self.assertEqual(smoke.parameter("name", "value"), b"\x04\x05namevalue")
        self.assertEqual(
            smoke.parameter("a" * 128, "b"),
            struct.pack("!I", 128 | 0x80000000) + b"\x01" + b"a" * 128 + b"b",
        )

    def test_record_padding(self):
        record = smoke.record(6, b"abc")
        self.assertEqual(struct.unpack("!BBHHBB", record[:8]), (1, 6, 1, 3, 5, 0))
        self.assertEqual(record[8:], b"abc" + bytes(5))

    def test_truncated_response_fails(self):
        sender, receiver = socket.socketpair()
        with sender, receiver:
            sender.sendall(b"abc")
            sender.shutdown(socket.SHUT_WR)
            with self.assertRaises(RuntimeError):
                smoke.receive(receiver, 8)

    def test_fragmented_response(self):
        sender, receiver = socket.socketpair()
        with sender, receiver:
            def send():
                for value in b"abcdefgh":
                    sender.sendall(bytes([value]))

            thread = threading.Thread(target=send)
            thread.start()
            self.assertEqual(smoke.receive(receiver, 8), b"abcdefgh")
            thread.join()


class SourceTests(unittest.TestCase):
    def metadata(self, checksum):
        return {
            "version": "8.5.12",
            "url": "https://www.php.net/distributions/php-8.5.12.tar.xz",
            "sha256": checksum,
        }

    def test_checksum_verified_before_archive_is_installed(self):
        content = b"official source fixture"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "source.tar.xz"
            with patch.object(source.urllib.request, "urlopen", return_value=io.BytesIO(content)):
                source.download(self.metadata(hashlib.sha256(content).hexdigest()), output)
            self.assertEqual(output.read_bytes(), content)
            self.assertFalse(output.with_suffix(".xz.partial").exists())

    def test_checksum_failure_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "source.tar.xz"
            output.write_bytes(b"previous verified archive")
            with patch.object(source.urllib.request, "urlopen", return_value=io.BytesIO(b"tampered")):
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    source.download(self.metadata("a" * 64), output)
            self.assertEqual(output.read_bytes(), b"previous verified archive")
            self.assertFalse(output.with_suffix(".xz.partial").exists())

    def test_rejects_alternate_download_host(self):
        with tempfile.TemporaryDirectory() as temporary:
            metadata = self.metadata("a" * 64)
            metadata["url"] = "https://example.invalid/source.tar.xz"
            with self.assertRaisesRegex(ValueError, "not the official"):
                source.download(metadata, Path(temporary) / "source.tar.xz")


class SnapshotTests(unittest.TestCase):
    def test_files_modes_and_symlinks_are_frozen(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source").write_bytes(b"source code")
            (root / "link").symlink_to("source")
            original = snapshot.inventory(root)
            self.assertEqual(original["source"]["sha256"], hashlib.sha256(b"source code").hexdigest())
            self.assertEqual(original["link"], {"link": "source"})
            (root / "input-manifest.json").write_text("{}")
            self.assertEqual(original, snapshot.inventory(root))
            (root / "source").write_bytes(b"modified source")
            self.assertNotEqual(original, snapshot.inventory(root))
            (root / "source").write_bytes(b"source code")
            (root / "source").chmod(0o700)
            self.assertNotEqual(original, snapshot.inventory(root))

    def test_gitiles_archive_digest_ignores_timestamps_but_not_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            digests = []
            normalized = []
            for name, timestamp, content in (
                ("first.tar.gz", 100, b"source"),
                ("second.tar.gz", 200, b"source"),
                ("changed.tar.gz", 200, b"modified"),
            ):
                path = root / name
                with tarfile.open(path, "w:gz") as archive:
                    member = tarfile.TarInfo("source.c")
                    member.size = len(content)
                    member.mtime = timestamp
                    member.mode = 0o644
                    archive.addfile(member, io.BytesIO(content))
                digests.append(overrides.tree_digest(path))
                destination = root / ("normalized-" + name)
                libaom.normalize(path, destination)
                self.assertEqual(
                    overrides.tree_digest(destination, "libaom/"), digests[-1]
                )
                with tarfile.open(destination) as archive:
                    self.assertEqual(archive.getnames(), ["libaom/source.c"])
                normalized.append(destination.read_bytes())
            self.assertEqual(digests[0], digests[1])
            self.assertNotEqual(digests[0], digests[2])
            self.assertEqual(normalized[0], normalized[1])
            self.assertNotEqual(normalized[0], normalized[2])

    def test_freeze_copies_rebuild_surfaces_and_removes_transient_credentials(self):
        scripts = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "log").mkdir()
            token = "fixture-" + os.urandom(16).hex()
            (root / "log/download.log").write_text(token)
            (root / ".spc.cache.php").write_text(token)
            result = subprocess.run(
                ["python3", str(scripts / "freeze-inputs.py"), str(root)],
                env={**os.environ, "GITHUB_TOKEN": token}, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "log").exists())
            self.assertFalse((root / ".spc.cache.php").exists())
            self.assertTrue((root / "runtime-build/.github/actions/php-macos-tools/action.yml").exists())
            self.assertTrue((root / "runtime-build/php/Resources/php/_4D_Execute_PHP.php").exists())
            self.assertEqual(json.loads((root / "input-manifest.json").read_text()), snapshot.inventory(root))

    def test_freeze_refuses_credentials_in_a_retained_file(self):
        scripts = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            token = "fixture-" + os.urandom(16).hex()
            (root / "retained.txt").write_text(token)
            result = subprocess.run(
                ["python3", str(scripts / "freeze-inputs.py"), str(root)],
                env={**os.environ, "GITHUB_TOKEN": token}, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("retained.txt", result.stderr)
            self.assertNotIn(token, result.stderr)
            self.assertFalse((root / "input-manifest.json").exists())


class LicenseTests(unittest.TestCase):
    def fixture(self, root, timestamp):
        (root / "downloads").mkdir(parents=True)
        (root / "downloads/.cache.json").write_text(json.dumps({
            "example": {"source": {"filename": "example.tar.gz"}, "binary": None},
        }))
        directory = root / "buildroot/license"
        directory.mkdir(parents=True)
        (directory / "example_LICENSE.txt").write_text("Example license\n")
        source = root / "source/example"
        source.mkdir(parents=True)
        (source / "LICENSE").write_text("Full upstream license text\n")
        (directory / "SUMMARY.json").write_text(json.dumps({
            "artifacts": {"example": {"license": "MIT", "dumped-at": timestamp}},
            "summary": {
                "total-artifacts": 1, "last-updated": timestamp,
                "license-types": {"MIT": ["example"]},
            },
        }))

    def test_timestamps_do_not_make_architecture_notices_differ(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = []
            for name in ("arm64", "x86_64"):
                directory = root / name
                self.fixture(directory, name)
                licenses.normalize(directory)
                results.append((directory / "buildroot/license/SUMMARY.json").read_bytes())
            self.assertEqual(results[0], results[1])
            self.assertTrue((directory / "buildroot/license/upstream/example/LICENSE").exists())

    def test_missing_notice_is_not_hidden_by_successful_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root, "test")
            (root / "buildroot/license/example_LICENSE.txt").unlink()
            with self.assertRaisesRegex(ValueError, "Missing or empty"):
                licenses.normalize(root)

    def test_missing_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root, "test")
            (root / "downloads/.cache.json").write_text('{"missing":{"source":{"filename":"x"}}}')
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                licenses.normalize(root)


@unittest.skipUnless(platform.system() == "Darwin" and shutil.which("clang"), "Requires macOS SDK")
class MachOTests(unittest.TestCase):
    scripts = Path(__file__).resolve().parent

    def compile(self, path, architecture, extra=()):
        subprocess.run(
            ["clang", "-arch", architecture, "-x", "c", "-", "-o", str(path), *extra],
            input=b"int main(void) { return 0; }\n", check=True, capture_output=True,
        )

    def verify(self, directory, architecture):
        return subprocess.run(
            ["bash", str(self.scripts / "verify-binaries.sh"), str(directory), architecture],
            capture_output=True, text=True,
        )

    def test_merge_and_verify_real_macho_slices(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for architecture in ("arm64", "x86_64"):
                directory = root / architecture
                directory.mkdir()
                self.compile(directory / "php", architecture)
                shutil.copy2(directory / "php", directory / "php-cgi")
                (directory / "licenses").mkdir()
                (directory / "licenses/fixture.txt").write_text("Test fixture\n")
                (directory / "input-manifest.json").write_text("{}\n")
                (directory / "BUILDING.md").write_text("Test fixture\n")
                (directory / "build-manifest.json").write_text(json.dumps({
                    "architecture": architecture, "version": "8.5.12",
                    "php_source": {"sha256": "a" * 64}, "builder_commit": "b" * 40,
                    "extensions": ["test"], "deployment_target": "13.0",
                    "libraries": [], "configuration": {}, "inputs_sha256": "c" * 64,
                }))
                result = self.verify(directory, architecture)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = root / "universal"
            result = subprocess.run(
                ["bash", str(self.scripts / "assemble.sh"), str(root), str(output)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads((output / "build-manifest.json").read_text())
            self.assertEqual(set(manifest["architectures"]), {"arm64", "x86_64"})
            self.assertNotIn("architecture", manifest)
            self.assertEqual(self.verify(output, "arm64").returncode, 1)
            manifest_path = root / "arm64/build-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["version"] = "8.5.11"
            manifest_path.write_text(json.dumps(manifest))
            result = subprocess.run(
                ["bash", str(self.scripts / "assemble.sh"), str(root), str(root / "mismatch")],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("manifests disagree on version", result.stderr)

    def test_rejects_runtime_search_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.compile(directory / "php", "arm64", ["-Wl,-rpath,/opt/homebrew/lib"])
            shutil.copy2(directory / "php", directory / "php-cgi")
            result = self.verify(directory, "arm64")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unexpected runtime search path", result.stderr)

    def test_rejects_non_system_dynamic_libraries(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            library = directory / "libfixture.dylib"
            subprocess.run(
                ["clang", "-arch", "arm64", "-dynamiclib", "-x", "c", "-",
                 "-Wl,-install_name,@rpath/libfixture.dylib", "-o", str(library)],
                input=b"int fixture(void) { return 42; }\n", check=True, capture_output=True,
            )
            self.compile(directory / "php", "arm64", [f"-Wl,-needed_library,{library}"])
            shutil.copy2(directory / "php", directory / "php-cgi")
            result = self.verify(directory, "arm64")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Non-system dynamic dependency", result.stderr)

    @unittest.skipUnless(shutil.which("pkg-config"), "Requires the pkg-config build tool")
    def test_build_wrapper_packages_verified_outputs_and_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder = root / "builder"
            builder.mkdir()
            LicenseTests().fixture(builder, "fixture")
            (builder / "bin").mkdir()
            engine = builder / "bin/spc"
            engine.write_text(
                '#!/bin/bash\nset -eu\n'
                'printf "%s\\n" "$*" >> invocations.log\n'
                'printf "%s\\n" "$SPC_EXTRA_PHP_VARS" >> invocations.log\n'
            )
            engine.chmod(0o755)
            binaries = builder / "buildroot/bin"
            binaries.mkdir()
            architecture = platform.machine()
            self.compile(binaries / "php", architecture)
            shutil.copy2(binaries / "php", binaries / "php-cgi")
            profile = {
                "builder_commit": "b" * 40, "deployment_target": "12.0",
                "extensions": ["bcmath"], "libraries": ["libjpeg"], "source_overrides": {},
                "php_configure_flags": "--enable-gd-jis-conv --without-pcre-jit",
            }
            (builder / "runtime-profile.json").write_text(json.dumps(profile))
            (builder / "php-release.json").write_text(json.dumps({
                "version": "8.5.12", "url": "https://www.php.net/distributions/php-8.5.12.tar.xz",
                "sha256": "a" * 64,
            }))
            inputs = builder / "input-manifest.json"
            inputs.write_text(json.dumps(snapshot.inventory(builder)))
            output = root / "output"
            result = subprocess.run(
                ["bash", str(self.scripts / "build.sh"), str(builder), str(output)],
                env={**os.environ, "EXPECTED_ARCH": architecture}, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads((output / "build-manifest.json").read_text())
            self.assertEqual(manifest["version"], "8.5.12")
            self.assertEqual(manifest["architecture"], architecture)
            self.assertEqual(manifest["configuration"], profile)
            self.assertEqual(manifest["inputs_sha256"], hashlib.sha256(inputs.read_bytes()).hexdigest())
            self.assertEqual((output / "input-manifest.json").read_bytes(), inputs.read_bytes())
            self.assertTrue((output / "BUILDING.md").exists())
            self.assertTrue((output / "licenses/example_LICENSE.txt").exists())
            calls = (builder / "invocations.log").read_text()
            self.assertIn("--disable-opcache-jit", calls)
            self.assertIn("--without-pcre-jit", calls)
            self.assertIn("--with-config-file-path=/etc/php", calls)
            self.assertIn("--for-packages=php,php-cli,php-cgi,libjpeg,ext-bcmath", calls)


@unittest.skipUnless(platform.system() == "Darwin" and shutil.which("clang"), "Requires macOS SDK")
class SigningTests(unittest.TestCase):
    def test_notary_acceptance_is_required_and_keychain_is_cleaned(self):
        for status in ("Accepted", "Invalid"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                runtime = root / "macOS"
                runtime.mkdir()
                fixture = MachOTests()
                for architecture in ("arm64", "x86_64"):
                    fixture.compile(root / architecture, architecture)
                subprocess.run(
                    ["lipo", "-create", str(root / "arm64"), str(root / "x86_64"),
                     "-output", str(runtime / "php")], check=True, capture_output=True,
                )
                shutil.copy2(runtime / "php", runtime / "php-cgi")
                (runtime / "build-manifest.json").write_text('{"version":"8.5.12"}')
                tools = root / "tools"
                tools.mkdir()
                mocks = {
                    "security": 'echo "$1" >> "$SECURITY_LOG"\n',
                    "codesign": """
                    if [ "$1" = --display ]; then
                        echo 'TeamIdentifier=TESTTEAM'
                        echo 'Authority=Developer ID Application: Fixture'
                        echo 'CodeDirectory flags=0x10000(runtime)'
                    fi
                    """,
                    "hdiutil": 'for arg in "$@"; do last="$arg"; done; touch "$last"\n',
                    "spctl": "exit 0\n",
                    "xcrun": """
                    if [ "$1" = notarytool ] && [ "$2" = submit ]; then
                        printf '{"id":"test-submission","status":"%s"}' "$NOTARY_STATUS"
                    elif [ "$1" = notarytool ] && [ "$2" = log ]; then
                        for arg in "$@"; do last="$arg"; done
                        echo '{}' > "$last"
                    fi
                    """,
                }
                for name, content in mocks.items():
                    executable = tools / name
                    executable.write_text("#!/bin/bash\nset -eu\n" + content)
                    executable.chmod(0o755)
                environment = {
                    **os.environ, "PATH": str(tools) + os.pathsep + os.environ["PATH"],
                    "APPLE_DEVELOPER_ID_CERTIFICATE": "Zml4dHVyZQ==",
                    "APPLE_DEVELOPER_ID_CERTIFICATE_PASSWORD": "fixture",
                    "CODESIGN_APPLE_ID": "Developer ID Application: Fixture",
                    "KEYCHAIN_PASSWORD": "fixture", "NOTARYTOOL_APPLE_ID": "fixture",
                    "NOTARYTOOL_PASSWORD": "fixture", "NOTARYTOOL_TEAM_ID": "TESTTEAM",
                    "NOTARY_STATUS": status, "SECURITY_LOG": str(root / "security.log"),
                }
                output = root / "distribution"
                result = subprocess.run(
                    ["bash", str(fixture.scripts / "sign-package.sh"), str(runtime), str(output)],
                    env=environment, capture_output=True, text=True,
                )
                log = (root / "security.log").read_text().splitlines()
                self.assertEqual(log[-1], "delete-keychain")
                self.assertEqual((output / "notary-log.json").read_text(), "{}\n")
                if status == "Accepted":
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertTrue((output / "SHA256SUMS").exists())
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse((output / "SHA256SUMS").exists())
                    self.assertIn("Invalid", result.stderr)


if __name__ == "__main__":
    unittest.main()
