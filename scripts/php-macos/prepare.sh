#!/bin/bash
set -euo pipefail

release="$(cd "$(dirname "${1:?usage: prepare.sh RELEASE_JSON INPUT_DIRECTORY}")" && pwd)/$(basename "$1")"
input="${2:?usage: prepare.sh RELEASE_JSON INPUT_DIRECTORY}"
scripts="$(cd "$(dirname "$0")" && pwd)"
if [[ -e "$input" ]]; then
    echo "Input directory must not already exist: ${input}" >&2
    exit 1
fi
repository="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["builder_repository"])' "$scripts/profile.json")"
commit="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["builder_commit"])' "$scripts/profile.json")"
git init --quiet "$input"
git -C "$input" remote add origin "$repository"
git -C "$input" fetch --quiet --depth 1 origin "$commit"
git -C "$input" checkout --quiet --detach FETCH_HEAD
[[ "$(git -C "$input" rev-parse HEAD)" == "$commit" ]]
input="$(cd "$input" && pwd)"
composer install --working-dir="$input" --no-dev --prefer-dist --no-interaction
git -C "$input" apply --check "$scripts/patches/sqlite-autosetup.patch"
git -C "$input" apply "$scripts/patches/sqlite-autosetup.patch"
cp "$release" "$input/php-release.json"
cp "$scripts/profile.json" "$input/runtime-profile.json"
extensions="$(python3 -c 'import json,sys; print(",".join(json.load(open(sys.argv[1]))["extensions"]))' "$scripts/profile.json")"
libraries="$(python3 -c 'import json,sys; print(",".join(json.load(open(sys.argv[1]))["libraries"]))' "$scripts/profile.json")"
version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$release")"
sqlite_url="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source_overrides"]["sqlite"]["url"])' "$scripts/profile.json")"
python3 "$scripts/normalize-libaom.py" "$scripts/profile.json" "$input/overrides"
libaom_url="file://$input/overrides/libaom-pinned.tar.gz"
packages="php,php-cli,php-cgi,$libraries"
IFS=',' read -r -a extension_names <<< "$extensions"
for extension in "${extension_names[@]}"; do
    packages="${packages},ext-${extension}"
done
(
    cd "$input"
    bin/spc download --for-packages="$packages" --without-suggests \
        --with-php="$version" --source-only --no-alt --no-interaction --retry=3 \
        --custom-url="sqlite:$sqlite_url" --custom-url="libaom:$libaom_url"
)
python3 "$scripts/download-source.py" "$release" "$input/downloads/php-$version.tar.xz"
python3 "$scripts/verify-overrides.py" "$input"
python3 "$scripts/freeze-inputs.py" "$input"
