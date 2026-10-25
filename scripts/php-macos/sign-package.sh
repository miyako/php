#!/bin/bash
set -euo pipefail
umask 077

directory="$(cd "${1:?usage: sign-package.sh DIRECTORY OUTPUT}" && pwd)"
mkdir -p "${2:?usage: sign-package.sh DIRECTORY OUTPUT}"
output="$(cd "$2" && pwd)"
scripts="$(cd "$(dirname "$0")" && pwd)"
: "${APPLE_DEVELOPER_ID_CERTIFICATE:?Missing signing certificate}"
: "${APPLE_DEVELOPER_ID_CERTIFICATE_PASSWORD:?Missing certificate password}"
: "${CODESIGN_APPLE_ID:?Missing Developer ID Application identity}"
: "${KEYCHAIN_PASSWORD:?Missing temporary keychain password}"
: "${NOTARYTOOL_APPLE_ID:?Missing notarization Apple ID}"
: "${NOTARYTOOL_PASSWORD:?Missing app-specific notarization password}"
: "${NOTARYTOOL_TEAM_ID:?Missing Apple developer team ID}"
bash "$scripts/verify-binaries.sh" "$directory"
version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$directory/build-manifest.json")"
[[ "$version" =~ ^[1-9][0-9]*\.[0-9]+\.[0-9]+$ ]]
basename="php-${version}-macos-universal"
temporary="$(mktemp -d "${TMPDIR:-/tmp}/php-sign.XXXXXX")"
keychain="${temporary}/signing.keychain-db"
created=false
cleanup() {
    status=$?
    if [[ "$created" == true ]]; then
        if ! security delete-keychain "$keychain"; then
            echo "Failed to remove temporary signing keychain: ${keychain}" >&2
            status=1
        fi
    fi
    rm -f "$temporary/certificate.p12"
    rmdir "$temporary"
    exit "$status"
}
trap cleanup EXIT
printf '%s' "$APPLE_DEVELOPER_ID_CERTIFICATE" | base64 --decode > "$temporary/certificate.p12"
security create-keychain -p "$KEYCHAIN_PASSWORD" "$keychain"
created=true
security set-keychain-settings -lut 21600 "$keychain"
security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$keychain"
security import "$temporary/certificate.p12" -k "$keychain" \
    -P "$APPLE_DEVELOPER_ID_CERTIFICATE_PASSWORD" -T /usr/bin/codesign
security set-key-partition-list -S apple-tool:,apple:,codesign: -s \
    -k "$KEYCHAIN_PASSWORD" "$keychain" > /dev/null

for executable in php php-cgi; do
    codesign --force --sign "$CODESIGN_APPLE_ID" --keychain "$keychain" \
        --options runtime --timestamp "$directory/$executable"
    codesign --verify --strict --all-architectures --verbose=2 "$directory/$executable"
    details="$(codesign --display --verbose=4 "$directory/$executable" 2>&1)"
    grep -Fx "TeamIdentifier=${NOTARYTOOL_TEAM_ID}" <<< "$details"
    grep -F 'Authority=Developer ID Application:' <<< "$details"
    grep -E 'flags=.*runtime' <<< "$details"
done

# Raw Mach-O executables cannot carry stapled tickets; distribute a stapled DMG too.
hdiutil create -quiet -format UDZO -volname "$basename" -srcfolder "$directory" "$output/$basename.dmg"
codesign --sign "$CODESIGN_APPLE_ID" --keychain "$keychain" --timestamp "$output/$basename.dmg"
codesign --verify --strict --verbose=2 "$output/$basename.dmg"
auth=(--apple-id "$NOTARYTOOL_APPLE_ID" --team-id "$NOTARYTOOL_TEAM_ID" --password "$NOTARYTOOL_PASSWORD")
notary_status=0
xcrun notarytool submit "$output/$basename.dmg" "${auth[@]}" \
    --wait --timeout 60m --output-format json > "$output/notary-result.json" || notary_status=$?
submission="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$output/notary-result.json")"
xcrun notarytool log "$submission" "${auth[@]}" "$output/notary-log.json"
if [[ "$notary_status" != 0 ]] || ! python3 -c \
    'import json,sys; sys.exit(json.load(open(sys.argv[1]))["status"] != "Accepted")' "$output/notary-result.json"; then
    cat "$output/notary-result.json" >&2
    cat "$output/notary-log.json" >&2
    exit 1
fi
xcrun stapler staple "$output/$basename.dmg"
xcrun stapler validate "$output/$basename.dmg"
spctl --assess --type open --context context:primary-signature --verbose=2 "$output/$basename.dmg"
ditto -c -k --sequesterRsrc --keepParent "$directory" "$output/$basename.zip"
(
    cd "$output"
    shasum -a 256 "$basename.dmg" "$basename.zip" > SHA256SUMS
)
