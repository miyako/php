#!/bin/bash
set -euo pipefail

slices="${1:?usage: assemble.sh SLICES OUTPUT}"
output="${2:?usage: assemble.sh SLICES OUTPUT}"
scripts="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$output"
for architecture in arm64 x86_64; do
    bash "$scripts/verify-binaries.sh" "$slices/$architecture" "$architecture"
done
for executable in php php-cgi; do
    lipo -create "$slices/arm64/$executable" "$slices/x86_64/$executable" -output "$output/$executable"
    chmod 755 "$output/$executable"
done
diff -r "$slices/arm64/licenses" "$slices/x86_64/licenses"
ditto "$slices/arm64/licenses" "$output/licenses"
cmp "$slices/arm64/input-manifest.json" "$slices/x86_64/input-manifest.json"
cp "$slices/arm64/input-manifest.json" "$output/input-manifest.json"
cp "$slices/arm64/BUILDING.md" "$output/BUILDING.md"
python3 - "$slices" "$output" <<'PY'
import json
from pathlib import Path
import sys

slices, output = map(Path, sys.argv[1:])
builds = {
    arch: json.loads((slices / arch / "build-manifest.json").read_text())
    for arch in ("arm64", "x86_64")
}
for field in ("version", "php_source", "builder_commit", "extensions", "libraries",
              "deployment_target", "inputs_sha256", "configuration"):
    if builds["arm64"][field] != builds["x86_64"][field]:
        raise SystemExit(f"Architecture build manifests disagree on {field}")
manifest = {**builds["arm64"], "architectures": builds}
manifest.pop("architecture")
(output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
PY
bash "$scripts/verify-binaries.sh" "$output"
