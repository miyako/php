# Official Windows PHP runtime

Once this workflow is on the default branch, run **Package Windows PHP** in
GitHub Actions. It downloads the latest official stable **x64 non-thread-safe
(NTS)** ZIP from [PHP for Windows](https://windows.php.net/download/), rather
than compiling a custom Windows interpreter.

`php_version=latest` first resolves the newest stable PHP release from php.net,
then requires the same version in the official Windows release index. If Windows
binaries lag the source release, the job fails rather than silently selecting an
older interpreter. An exact version is supported only while listed in
`https://windows.php.net/downloads/releases/releases.json`.

## Package contents and integrity

The ZIP is checked against the SHA-256 in the official release metadata before
extraction. Core EXE/DLL architecture is verified as x64, `php8.dll` is required,
and a TS `php8ts.dll` is rejected. The `Win32` substring in the upstream ZIP name
does not mean this is a 32-bit build.

All official files are retained, including optional extension DLLs, dependency
DLLs, redistribution notices, upstream example INIs, and upstream SBOMs where
provided. Official EXE/DLL contents are never patched or re-signed.

The configured runtime additionally contains:

| File | Purpose |
| --- | --- |
| `php.ini` | Explicit extension loading and relocatable certificate paths |
| `extras/ssl/cacert.pem` | SHA-256-pinned, dated Mozilla CA bundle from curl.se |
| `extras/ssl/MPL-2.0.txt` | The CA bundle's license |
| `runtime-manifest.json` | Official ZIP URL/hash, complete configuration profile, and per-file SHA-256 |
| `authenticode.json` | Windows-native signature status and SHA-256 for every EXE/DLL |
| `BUILDING.md` | These instructions |

`profile.json` selects the required extensions, including mbstring, OpenSSL,
curl, SQLite/PDO SQLite, mysqli, GD, GMP, LDAP, tidy, sockets, and ZIP. mbstring
loads before exif. POSIX is not available on Windows. Optional upstream DLLs
remain available but are not all enabled automatically.

The CA bundle uses Mozilla trust, not automatic Windows enterprise-root trust.
Its immutable dated URL and checksum must be reviewed together when updating
`profile.json`. Both curl and PHP streams use the bundled PEM; certificate
verification is never disabled.

## 4D configuration and relocation

The component prefers `/RESOURCES/bin/Windows/php.ini` for Windows CLI,
interactive, and FastCGI workers when that file exists. An explicitly supplied
INI is still honored. Existing installations without the new runtime INI retain
their old configuration selection; the old `/RESOURCES/php/php.ini` is not
overwritten.

The worker's `_4D_PHP_RUNTIME` environment variable points to the runtime folder.
The generated INI uses `${_4D_PHP_RUNTIME}` for extension and CA paths. It remains
valid when `PHP_CGI` copies it into `/LOGS/php-cgi.ini` and substitutes its
`auto_prepend_file` bridge. Workers still run from the temporary directory:
extension loading does not depend on the current working directory.
The worker defaults `PHP_INI_SCAN_DIR` to empty so machine-wide scan directories
cannot inject incompatible extensions. A custom controller can explicitly set
its own scan directory; an explicit custom INI file is never replaced.

For a custom INI with the same modules, copy/edit the new runtime INI rather than
the old shared template, which enables fewer DLL extensions.

For direct PowerShell use outside 4D:

```powershell
$env:_4D_PHP_RUNTIME = (Resolve-Path ./Windows).Path
$env:PHP_INI_SCAN_DIR = ''
& "$env:_4D_PHP_RUNTIME/php.exe" -c "$env:_4D_PHP_RUNTIME/php.ini" -r 'echo PHP_VERSION;'
```

Use the Windows versions supported by PHP and install the appropriate
[Microsoft Visual C++ x64 Redistributable](https://www.php.net/manual/en/install.windows.requirements.php).
The pipeline uses Windows Server 2025, whose image already includes the runtime;
it does not copy Microsoft runtime DLLs from the runner into the distribution.
NTS is intended for CLI/FastCGI, not an Apache in-process TS module.

## Authenticode and publication

Every EXE/DLL is inspected with Windows `Get-AuthenticodeSignature`. Existing
valid signatures are preserved. **Upstream unsigned files are allowed and
reported as `NotSigned`; this pipeline does not claim to sign them.** Any other
status, such as `HashMismatch`, `NotTrusted`, or `UnknownError`, fails the job.
Reports are bound to each file's SHA-256 and checked again before packaging.
No Apple or Windows signing secrets are required.

Native Windows tests use a relocated folder containing spaces, a non-runtime
working directory, the generated INI, a copied FastCGI INI, and the real 4D PHP
function bridge. They exercise CLI, interactive stdin, extensions, trusted and
untrusted TLS, and repeated TCP FastCGI requests. The final ZIP is extracted and
tested again before publication.

The `php-windows-runtime` artifact contains
`php-VERSION-windows-x64-nts.zip` and `SHA256SUMS`; its ZIP contains a `Windows/`
folder. `php-windows-upstream` retains the original ZIP and resolved release
metadata for provenance. `publish=true` creates a separate
`php-runtime-windows-VERSION-RUN_ID` release; it never changes the component's
latest release. Scheduled and PR runs only produce artifacts.

## Updating the vendored runtime

This infrastructure does not overwrite the checked-in PHP 8.3.2 binaries.
After a native Windows run succeeds, verify `SHA256SUMS`, stop PHP workers and
4D, and **replace the entire** `php/Resources/bin/Windows/` directory with the
extracted `Windows/` folder. Do not overlay NTS onto TS, keep old extension DLLs,
or copy only `php.exe`: PHP, extensions, dependencies, and INI must match.
Restart 4D so its shared FastCGI singleton selects the new configuration.

Keep the redistribution notices, manifests, certificate bundle, and CA license.
GitHub Actions artifacts expire; publish a release when retaining a distribution.
Keep the matching upstream ZIP/release metadata if reproducibility is required.

## Maintenance

The packaging tools use Python 3.11+ and standard-library dependencies only:

```sh
python3 scripts/php-windows/test-tools.py
python3 scripts/php-windows/package.py resolve --output build/windows-release.json
python3 scripts/php-windows/package.py prepare --release build/windows-release.json \
  --archive build/upstream.zip --output build/Windows
```

Preparation can run on macOS/Linux for inspection; native execution and
Authenticode inspection require Windows. Output must be a fresh directory.
On Windows, run the workflow's signature, smoke-test, and archive commands.
The TLS rejection fixture uses OpenSSL from Git for Windows
(`C:\Program Files\Git\usr\bin\openssl.exe`), or a supplied `--openssl` path.
For an older saved release, provide its previously verified ZIP through
`--archive`; no older version is guessed from today's release index.
