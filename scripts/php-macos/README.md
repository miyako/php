# macOS PHP runtime

Once the workflow is merged into the default branch, run **Build macOS PHP** in
GitHub Actions. `php_version=latest` resolves the newest
stable release from [PHP's official release metadata](https://www.php.net/releases/index.php?json),
once for both builds, and verifies the source archive's SHA-256. An explicit
version such as `8.5.12` is also supported. Development snapshots and release
candidates are not selected. PHP 8.5.12 was the latest stable release when this
pipeline was added.

The pipeline builds native `arm64` and `x86_64` slices on separate macOS runners,
then combines each pair with `lipo`. Both `php` (CLI) and `php-cgi` (persistent
FastCGI, including `-b`) are produced. It does not substitute PHP-FPM for
`php-cgi`. Tests execute the universal binaries on both native architectures
before and after signing, exercise the static extensions, send real TCP FastCGI
requests using the component's `-b address:port` invocation, and call
`_4D_Execute_PHP.php` through the function bridge. The smoke test also supports
Unix sockets with `--transport unix`.

The build engine is [static-php-cli](https://github.com/crazywhalecc/static-php-cli),
pinned by commit in `profile.json`. A preparation job resolves the complete
dependency graph **once**, then archives the downloaded sources, Composer
dependencies, builder, and this repository's build scripts. Both native jobs use
that same SHA-256-checked snapshot. `input-manifest.json` records every input file,
mode, and symlink; its hash is included in the runtime's build manifest. A new run
can resolve newer dependency releases, but the two slices of one runtime never
independently select them. This is a reproducible input snapshot, not a guarantee
of bit-for-bit identical binaries or Apple signing timestamps.

`profile.json` also replaces the builder's old SQLite recipe source with the
official **SQLite 3.54.1** archive, verified using SQLite's published SHA3-256.
The checked-in builder patch removes obsolete Autoconf PIC options rejected by
SQLite's modern Autosetup configuration and supplies `-fPIC` directly instead.
AVIF's libaom dependency is fixed to the **3.15.2** release commit rather than
floating `main`. Gitiles regenerates archive headers, so its pinned checksum
covers a canonical inventory of source-file contents, modes, and symlink targets;
the shared snapshot additionally hashes the exact downloaded archive bytes.
The verified libaom archive is repacked with the single top-level directory
expected by the builder's extractor, without changing source contents.

The deployment target is **macOS 12.0**. Current CI tests on macOS 15; setting a
deployment target alone does not establish compatibility with every older OS.
The extension contract preserves the checked-in runtime's modules, including GD
JPEG/WebP/AVIF/JIS and mbstring regex support. Readline uses BSD-licensed **libedit**
instead of GNU Readline; editing/key-binding behavior can differ. LDAP SASL is
disabled, as in the existing runtime.

`modules.txt` is a required-module contract, not a claim that every optional
feature of the old Homebrew-derived libraries is reproduced. Additional curl
protocols and ZIP compression codecs require explicit dependency selection and
matching tests before distribution.

## Static linking

Completely static executables are not supported by Apple's macOS SDK.
Third-party dependencies are built as static archives. Only `/usr/lib/` and
`/System/Library/Frameworks/` dynamic dependencies are allowed; Homebrew paths,
`@rpath`, `@loader_path`, and additional runtime search paths fail the build.
The artifacts need neither Homebrew nor a separate extension directory.

This replaces the manual architecture switching and Homebrew bottle extraction
described in [miyako/4d-topic-php](https://github.com/miyako/4d-topic-php).
No generated PHP headers or SQLite/iconv implementation files are hand-patched.
Each distribution includes a build manifest and dependency licenses; the
component's MIT license does not replace PHP's or its dependencies' licenses.
The runtime includes both the builder's notices and upstream license, copying,
copyright, notice, and patent files from each dependency and PHP's bundled
libraries, retaining their source-relative paths under `licenses/upstream/`.

HTTPS uses OpenSSL's `/etc/ssl/cert.pem` system-file trust store, **not** the
Homebrew certificate directory and **not** automatic Apple Keychain trust.
CI checks this path and verifies HTTPS through both curl and PHP streams after
relocation, including rejection of an untrusted local certificate. Custom
enterprise roots require explicit PHP/OpenSSL configuration.

## Signing and notarization

Signing is enabled by default for manual and reusable workflow invocations.
The pipeline uses the same repository secret names as the component publisher:

| Secret | Value |
| --- | --- |
| `APPLE_DEVELOPER_ID_CERTIFICATE` | Base64-encoded Developer ID Application `.p12`, including its private key |
| `APPLE_DEVELOPER_ID_CERTIFICATE_PASSWORD` | Password protecting that `.p12` |
| `CODESIGN_APPLE_ID` | Full Developer ID Application signing identity, not an email address |
| `KEYCHAIN_PASSWORD` | Strong password for a temporary build-only keychain |
| `NOTARYTOOL_APPLE_ID` | Apple ID authorized for notarization |
| `NOTARYTOOL_TEAM_ID` | Developer team's identifier |
| `NOTARYTOOL_PASSWORD` | App-specific password for the notarization Apple ID |

The identity's team must match `NOTARYTOOL_TEAM_ID`. The signing script creates
an isolated keychain and removes it on exit. Missing credentials, signature
failures, non-`Accepted` notarization results, and failed ticket validation stop
the workflow. Submission results and Apple's detailed logs are saved as
diagnostic artifacts. No production credentials are needed for unsigned PR
builds or weekly checks.

Both universal executables receive Developer ID signatures with hardened runtime
and secure timestamps. OPcache and PCRE JIT are disabled at build time; regular
expressions still work, but without JIT acceleration. No executable-memory or
library-validation exceptions are granted. They are packaged in a signed DMG, submitted with
`notarytool`, and the accepted ticket is stapled to the DMG. A ZIP with the same
signed executables is also provided, with SHA-256 checksums for both containers.
**Raw CLI executables and ZIP files cannot be stapled.** Use the stapled DMG for
offline ticket verification; a downloaded ZIP can require an online Gatekeeper
lookup. Notarization of this runtime does not notarize an application that
subsequently embeds or re-signs it: that application must be notarized separately.

`sign=false` produces only the explicitly unsigned universal artifact and skips
notarization. `publish=true` with signing enabled creates a separate
`php-runtime-VERSION-RUN_ID` GitHub release after both native signed tests pass;
it never marks the runtime as the component's latest release.

When distributing the runtime, publish and retain the matching source snapshot
as well. GMP and iconv introduce LGPL obligations for static linking; the
complete source inputs and build recipes are provided so recipients can rebuild
with modified libraries. Do not distribute just the executables and discard the
source kit. Review all dependency licenses and applicable redistribution
obligations before shipping; copying notices alone is not a compliance guarantee.

## Artifacts and use in the component

The `php-macos-universal` workflow artifact contains an unsigned
`php-macos-universal.zip`. The `php-macos-signed` artifact contains the signed
runtime ZIP, stapled DMG, and `SHA256SUMS`. Archives preserve executable modes;
GitHub's outer artifact ZIP alone does not preserve Unix permissions.

The inner runtime ZIP contains a `macOS/` directory, with `php`, `php-cgi`,
`build-manifest.json`, and `licenses/`. To update the vendored runtime, verify
`SHA256SUMS`, extract the inner ZIP using `ditto -x -k`, and replace
`php/Resources/bin/macOS/` with that directory. Keep the license notices and
manifest alongside the executables. Do not run `lipo`, `strip`, or other binary
modification tools after signing.

The `php-macos-build-inputs` artifact contains
`php-macos-build-inputs.tar.gz` and `SOURCE-SHA256SUMS`. Published runtime releases
include these source assets too. GitHub Actions artifacts expire, so artifact
storage alone is not a permanent source-distribution mechanism.

Building this infrastructure does not itself replace the currently checked-in
binaries: a successful macOS build and, for distribution, access to the Apple
credentials are required first.

## Maintenance

To build a native slice locally, install Xcode command-line tools, Python 3.11+,
PHP 8.4+, Composer, and the Homebrew tools listed in
`.github/actions/php-macos-tools/action.yml`. Put Homebrew Bison and Flex first
on `PATH`. From the repository root:

```sh
python3 scripts/php-macos/resolve-release.py --output build/php-release.json
bash scripts/php-macos/prepare.sh build/php-release.json build/php-macos-input
bash scripts/php-macos/build.sh build/php-macos-input "build/slices/$(uname -m)"
python3 scripts/php-macos/smoke-test.py "build/slices/$(uname -m)" \
  --modules scripts/php-macos/modules.txt --tls --system-ca --features
```

`prepare.sh` requires a fresh input directory. To rebuild from a published source
kit, verify `SOURCE-SHA256SUMS`, extract it under `build/`, and invoke `build.sh`
instead of preparing new sources. Use the bundled `runtime-build/` scripts for
that release, not a newer checkout's scripts. Building the other architecture
requires another native macOS host; the builder does not support Darwin cross
compilation. Collect both slice directories, then run:

```sh
bash scripts/php-macos/assemble.sh build/slices build/macOS
bash scripts/php-macos/sign-package.sh build/macOS build/distribution
```

The final command requires the signing variables listed above in the environment.

Run the helper tests with `python3 scripts/php-macos/test-tools.py`, and lint the
shell scripts and workflow with `shellcheck` and `actionlint`. On macOS the helper
tests also compile actual Mach-O fixtures and verify merging, architecture checks,
and rejection of runtime search paths. The smoke test can be run against an
existing runtime directory:

```sh
python3 scripts/php-macos/smoke-test.py php/Resources/bin/macOS
```

New upstream versions must pass the extension contract and dynamic-link audit;
there is no silent fallback to the old vendored PHP if a build fails.
