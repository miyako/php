#!/bin/bash
set -euo pipefail

input="$(cd "${1:?usage: build.sh INPUT_DIRECTORY OUTPUT_DIRECTORY}" && pwd)"
mkdir -p "${2:?usage: build.sh INPUT_DIRECTORY OUTPUT_DIRECTORY}"
output="$(cd "$2" && pwd)"
scripts="$(cd "$(dirname "$0")" && pwd)"
architecture="$(uname -m)"
if [[ "$architecture" != "${EXPECTED_ARCH:-$architecture}" ]]; then
    echo "Build must run natively on ${EXPECTED_ARCH}, not ${architecture}" >&2
    exit 1
fi
case "$architecture" in
    arm64) tool_architecture=aarch64 ;;
    x86_64) tool_architecture=x86_64 ;;
    *) echo "Unsupported macOS architecture: ${architecture}" >&2; exit 1 ;;
esac
if [[ "$(uname -s)" != Darwin ]]; then
    echo "This build requires a native macOS host." >&2
    exit 1
fi
python3 "$scripts/snapshot.py" verify "$input"
python3 "$scripts/verify-overrides.py" "$input"
tool_directory="$input/pkgroot/$tool_architecture-darwin/bin"
mkdir -p "$tool_directory"
if [[ ! -e "$tool_directory/pkg-config" ]]; then
    ln -s "$(command -v pkg-config)" "$tool_directory/pkg-config"
fi
extensions="$(python3 -c 'import json,sys; print(",".join(json.load(open(sys.argv[1]))["extensions"]))' "$input/runtime-profile.json")"
libraries="$(python3 -c 'import json,sys; print(",".join(json.load(open(sys.argv[1]))["libraries"]))' "$input/runtime-profile.json")"
MACOSX_DEPLOYMENT_TARGET="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["deployment_target"])' "$input/runtime-profile.json")"
export MACOSX_DEPLOYMENT_TARGET
SPC_EXTRA_PHP_VARS="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["php_configure_flags"])' "$input/runtime-profile.json")"
export SPC_EXTRA_PHP_VARS
packages="php,php-cli,php-cgi,$libraries"
IFS=',' read -r -a extension_names <<< "$extensions"
for extension in "${extension_names[@]}"; do
    packages="${packages},ext-${extension}"
done
(
    cd "$input"
    bin/spc doctor --no-interaction
    bin/spc build:php "$extensions" --build-cli --build-cgi \
        --with-packages="$libraries" --no-download --disable-opcache-jit \
        --with-config-file-path=/etc/php --with-config-file-scan-dir=/etc/php/conf.d \
        --no-interaction
    bin/spc dump-license --for-packages="$packages" --without-suggests --no-interaction -vv 2>&1 | tee license-dump.log
    if grep -E 'Artifact not found, skipping:|Failed to dump license for|License file not found for|Artifact source not extracted:|No metadata for artifact:|No license files specified for:' license-dump.log; then
        echo "License collection was incomplete; refusing to distribute." >&2
        exit 1
    fi
)
python3 "$scripts/normalize-licenses.py" "$input"
cp "$input/buildroot/bin/php" "$input/buildroot/bin/php-cgi" "$output/"
ditto "$input/buildroot/license" "$output/licenses"
cp "$input/input-manifest.json" "$output/input-manifest.json"
cp "$scripts/README.md" "$output/BUILDING.md"
python3 - "$input" "$output" "$architecture" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root, output = map(Path, sys.argv[1:3])
profile = json.loads((root / "runtime-profile.json").read_text())
release = json.loads((root / "php-release.json").read_text())
manifest = {
    "version": release["version"], "php_source": release,
    "builder_commit": profile["builder_commit"],
    "architecture": sys.argv[3], "deployment_target": profile["deployment_target"],
    "extensions": profile["extensions"], "libraries": profile["libraries"],
    "inputs_sha256": hashlib.sha256((root / "input-manifest.json").read_bytes()).hexdigest(),
    "configuration": profile,
    "macos_build_host": subprocess.check_output(["sw_vers", "-productVersion"], text=True).strip(),
    "compiler": subprocess.check_output(["clang", "--version"], text=True).splitlines()[0],
    "ca_bundle": "/etc/ssl/cert.pem",
}
(output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
PY
bash "$scripts/verify-binaries.sh" "$output" "$architecture"
