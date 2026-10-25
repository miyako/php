#!/bin/bash
set -euo pipefail

directory="${1:?usage: verify-binaries.sh DIRECTORY [ARCH]}"
architecture="${2:-universal}"
for executable in php php-cgi; do
    binary="${directory}/${executable}"
    test -x "$binary"
    if [[ "$architecture" == universal ]]; then
        lipo "$binary" -verify_arch arm64 x86_64
        if [[ "$(lipo -archs "$binary" | wc -w | tr -d ' ')" != 2 ]]; then
            echo "Expected exactly two architecture slices in ${binary}" >&2
            exit 1
        fi
    else
        if [[ "$(lipo -archs "$binary")" != "$architecture" ]]; then
            echo "Expected only ${architecture} in ${binary}" >&2
            exit 1
        fi
    fi
    dependencies="$(otool -arch all -L "$binary" | awk '/^\t/ {print $1}' | sort -u)"
    [[ -n "$dependencies" ]]
    while IFS= read -r dependency; do
        case "$dependency" in
            /usr/lib/*|/System/Library/Frameworks/*) ;;
            *) echo "Non-system dynamic dependency in ${binary}: ${dependency}" >&2; exit 1 ;;
        esac
    done <<< "$dependencies"
    if otool -arch all -l "$binary" | grep 'cmd LC_RPATH' > /dev/null; then
        echo "Unexpected runtime search path in ${binary}" >&2
        exit 1
    fi
    printf '%s\n%s\n' "$binary" "$dependencies"
done
