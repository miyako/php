#!/usr/bin/env python3
"""Test official NTS PHP with the same relocatable configuration used by 4D."""

import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--openssl", default=shutil.which("openssl"))
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("The native Windows runtime test must run on Windows")
    if not args.openssl or not Path(args.openssl).is_file():
        parser.error("--openssl must point to OpenSSL (Git for Windows includes usr/bin/openssl.exe)")
    helper = Path(__file__).resolve().parents[1] / "php-macos/smoke-test.py"
    spec = importlib.util.spec_from_file_location("fastcgi", helper)
    fastcgi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fastcgi)
    manifest = json.loads((args.directory / "runtime-manifest.json").read_text())
    with tempfile.TemporaryDirectory(prefix="PHP runtime with spaces ") as temporary:
        root = Path(temporary)
        runtime = root / "Windows"
        shutil.copytree(args.directory, runtime)
        environment = {
            key: value for key, value in os.environ.items()
            if key not in ("PHPRC", "SSL_CERT_FILE", "SSL_CERT_DIR", "CURL_CA_BUNDLE",
                           "PHP_FCGI_CHILDREN", "PHP_FCGI_MAX_REQUESTS", "FCGI_WEB_SERVER_ADDRS")
        }
        environment.update({"_4D_PHP_RUNTIME": str(runtime) + os.sep, "PHP_INI_SCAN_DIR": ""})
        ini = runtime / "php.ini"
        cli = [str(runtime / "php.exe"), "-c", str(ini)]
        required = manifest["profile"]["required_modules"]
        probe = """
        foreach (json_decode(getenv('PHP_TEST_MODULES'), true) as $extension) {
            if (!extension_loaded($extension)) { throw new RuntimeException('Missing: '.$extension); }
        }
        if (PHP_ZTS || PHP_INT_SIZE !== 8) { throw new RuntimeException('Expected x64 NTS'); }
        $db = new SQLite3(':memory:');
        $pdo = new PDO('sqlite::memory:');
        $zip = new ZipArchive();
        if ($db->querySingle('SELECT 42') !== 42
            || $pdo->query('SELECT 42')->fetchColumn() != 42
            || mb_strlen('日本語', 'UTF-8') !== 3
            || !function_exists('mb_ereg')
            || (string) simplexml_load_string('<v>42</v>') !== '42'
            || gmp_strval(gmp_add(40, 2)) !== '42'
            || gzdecode(gzencode('ok')) !== 'ok'
            || strlen(openssl_random_pseudo_bytes(16)) !== 16) {
            throw new RuntimeException('Extension probe failed');
        }
        echo json_encode(['sapi' => PHP_SAPI, 'version' => PHP_VERSION]);
        """
        environment["PHP_TEST_MODULES"] = json.dumps(required)

        def run(arguments, **options):
            result = subprocess.run(
                arguments, env=environment, cwd=root, check=True,
                capture_output=True, timeout=45, **options,
            )
            if result.stderr:
                raise RuntimeError(f"PHP startup/runtime warnings: {result.stderr!r}")
            return result.stdout

        result = fastcgi.decode_json(run(cli + ["-r", probe]), "Windows CLI")
        if result != {"sapi": "cli", "version": manifest["release"]["version"]}:
            raise RuntimeError(f"Unexpected Windows runtime: {result}")
        interactive = run(cli + ["-a"], input=b"echo '4D_INTERACTIVE_OK';\r\nexit;\r\n")
        if b"4D_INTERACTIVE_OK" not in interactive:
            raise RuntimeError(f"Interactive worker failed: {interactive!r}")
        run(cli + ["-r", """
        $curl = curl_init('https://www.php.net/');
        curl_setopt_array($curl, [
            CURLOPT_NOBODY => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 30,
            CURLOPT_SSL_VERIFYPEER => true, CURLOPT_SSL_VERIFYHOST => 2,
        ]);
        if (curl_exec($curl) === false) { throw new RuntimeException(curl_error($curl)); }
        $socket = stream_socket_client('tls://www.php.net:443', $errno, $error, 30);
        if ($socket === false) { throw new RuntimeException($error); }
        fclose($socket);
        """])
        fastcgi.reject_untrusted_tls(cli, environment, openssl=args.openssl)
        bridge = Path(__file__).resolve().parents[2] / "php/Resources/php/_4D_Execute_PHP.php"
        copied_ini = root / "php-cgi.ini"
        config = ini.read_text().replace(
            ";auto_prepend_file =", f'auto_prepend_file = "{bridge.as_posix()}"'
        )
        copied_ini.write_text(config, encoding="utf-8")
        script = root / "probe.php"
        script.write_text("<?php\n" + probe, encoding="utf-8")
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            address = reservation.getsockname()
        with (root / "cgi.log").open("w+") as log:
            process = subprocess.Popen(
                [str(runtime / "php-cgi.exe"), "-c", str(copied_ini),
                 "-b", f"{address[0]}:{address[1]}"],
                cwd=root, env=environment, stdout=log, stderr=log,
            )
            try:
                deadline = time.monotonic() + 20
                while True:
                    if process.poll() is not None or time.monotonic() >= deadline:
                        log.seek(0)
                        raise RuntimeError(f"Windows FastCGI did not start: {log.read()}")
                    with socket.socket() as connection:
                        connection.settimeout(0.2)
                        if connection.connect_ex(address) == 0:
                            break
                    time.sleep(0.05)
                parameters = {
                    "SCRIPT_FILENAME": str(script), "SCRIPT_NAME": "/probe.php",
                    "REQUEST_METHOD": "GET", "REDIRECT_STATUS": "200",
                    "SERVER_PROTOCOL": "HTTP/1.1", "GATEWAY_INTERFACE": "CGI/1.1",
                }
                for _ in range(2):
                    headers, body = fastcgi.request(address, parameters)
                    if headers.get("Status", "200 OK") != "200 OK" or fastcgi.decode_json(
                        body, "Windows FastCGI"
                    ) != {"sapi": "cgi-fcgi", "version": manifest["release"]["version"]}:
                        raise RuntimeError(f"Unexpected Windows FastCGI response: {headers}, {body!r}")
                headers, body = fastcgi.request(address, {
                    **parameters, "_4D_IsCalledFrom4D": "yes", "_4D_ScriptPath": "php_command",
                    "_4D_FunctionName": "strtoupper", "_4D_FunctionParams": '["hello"]',
                    "_4D_IsWindows": "yes", "_4D_WindowsCodePage": "UTF-8",
                })
                if headers.get("X-4D-FunctionResult") != base64.b64encode(b"HELLO").decode():
                    raise RuntimeError(f"4D function bridge failed: {headers}, {body!r}")
            finally:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            log.seek(0)
            diagnostics = log.read()
            if diagnostics.strip():
                raise RuntimeError(f"Windows FastCGI wrote startup/runtime diagnostics: {diagnostics}")
    print(f"PHP {manifest['release']['version']}: Windows x64 NTS, CLI, interactive, TLS, and 4D FastCGI OK")


if __name__ == "__main__":
    main()
