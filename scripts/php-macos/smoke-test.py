#!/usr/bin/env python3
"""Exercise CLI, FastCGI, and 4D's function-call bridge without external clients."""

import argparse
import base64
import http.server
import json
import os
from pathlib import Path
import socket
import ssl
import struct
import subprocess
import tempfile
import threading
import time


def record(kind, content=b""):
    padding = (-len(content)) % 8
    return struct.pack("!BBHHBB", 1, kind, 1, len(content), padding, 0) + content + bytes(padding)


def parameter(key, value):
    key, value = key.encode(), value.encode()

    def length(size):
        return bytes([size]) if size < 128 else struct.pack("!I", size | 0x80000000)

    return length(len(key)) + length(len(value)) + key + value


def receive(connection, size):
    result = b""
    while len(result) < size:
        chunk = connection.recv(size - len(result))
        if not chunk:
            raise RuntimeError("FastCGI closed the connection before END_REQUEST")
        result += chunk
    return result


def decode_json(output, label):
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{label} did not return clean JSON:\n{output.decode(errors='replace')}") from error


def request(address, parameters):
    with socket.socket(socket.AF_INET if isinstance(address, tuple) else socket.AF_UNIX) as connection:
        connection.settimeout(15)
        connection.connect(address)
        content = b"".join(parameter(key, value) for key, value in parameters.items())
        connection.sendall(
            record(1, struct.pack("!HB5x", 1, 0))
            + record(4, content) + record(4) + record(5)
        )
        output = b""
        errors = b""
        while True:
            version, kind, request_id, size, padding, _ = struct.unpack(
                "!BBHHBB", receive(connection, 8)
            )
            if version != 1 or request_id != 1:
                raise RuntimeError("Invalid FastCGI record")
            content = receive(connection, size)
            receive(connection, padding)
            if kind == 6:
                output += content
            elif kind == 7:
                errors += content
            elif kind == 3:
                application_status, protocol_status = struct.unpack("!IB3x", content)
                if application_status or protocol_status or errors:
                    raise RuntimeError(f"FastCGI failed: {content!r}, stderr={errors!r}")
                headers, body = output.split(b"\r\n\r\n", 1)
                return dict(
                    line.decode().split(": ", 1) for line in headers.split(b"\r\n")
                ), body


def reject_untrusted_tls(cli, environment, openssl="/usr/bin/openssl"):
    with tempfile.TemporaryDirectory(prefix="php-tls-") as temporary:
        root = Path(temporary)
        subprocess.run(
            [openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes",
             "-subj", "/CN=localhost", "-days", "1", "-keyout", str(root / "key.pem"),
             "-out", str(root / "cert.pem")],
            check=True, capture_output=True,
        )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(root / "cert.pem", root / "key.pem")
        with http.server.HTTPServer(("127.0.0.1", 0), http.server.BaseHTTPRequestHandler) as server:
            server.socket = context.wrap_socket(server.socket, server_side=True)
            server.timeout = 10
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                subprocess.run(cli + ["-r", f"""
                $curl = curl_init('https://localhost:{port}/');
                curl_setopt_array($curl, [
                    CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 10,
                    CURLOPT_SSL_VERIFYPEER => true, CURLOPT_SSL_VERIFYHOST => 2,
                ]);
                if (curl_exec($curl) !== false || curl_errno($curl) !== 60) {{
                    throw new RuntimeException('curl did not reject an untrusted certificate');
                }}
                $warnings = [];
                set_error_handler(static function ($severity, $message) use (&$warnings) {{
                    $warnings[] = $message;
                    return true;
                }});
                $socket = stream_socket_client('tls://localhost:{port}', $errno, $message, 10);
                restore_error_handler();
                if ($socket !== false) {{
                    fclose($socket);
                    throw new RuntimeException('PHP streams accepted an untrusted certificate');
                }}
                if (stripos(implode('\\n', $warnings), 'certificate verify failed') === false) {{
                    throw new RuntimeException('PHP stream failed for a reason other than certificate trust');
                }}
                """], env=environment, check=True, timeout=30)
            finally:
                server.shutdown()
                thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--version")
    parser.add_argument("--arch", choices=("arm64", "x86_64"))
    parser.add_argument("--modules", type=Path)
    parser.add_argument("--tls", action="store_true", help="Verify HTTPS trust without build-machine CA overrides")
    parser.add_argument("--system-ca", action="store_true", help="Require the macOS system CA file, not Homebrew")
    parser.add_argument("--features", action="store_true", help="Check GD formats and the selected libedit backend")
    parser.add_argument("--transport", choices=("tcp", "unix"), default="tcp")
    args = parser.parse_args()
    prefix = ["/usr/bin/arch", f"-{args.arch}"] if args.arch else []
    directory = args.directory.resolve()
    cli = prefix + [str(directory / "php"), "-n"]
    environment = {
        key: value for key, value in os.environ.items()
        if key not in ("SSL_CERT_FILE", "SSL_CERT_DIR", "CURL_CA_BUNDLE", "PHPRC")
    }
    environment["PHP_INI_SCAN_DIR"] = ""
    version = subprocess.check_output(cli + ["-r", "echo PHP_VERSION;"], env=environment).decode()
    if args.version and version != args.version:
        raise RuntimeError(f"Expected PHP {args.version}, found {version}")
    expected = set(args.modules.read_text().split()) if args.modules else set()
    if expected:
        actual = set(decode_json(subprocess.check_output(
            cli + ["-r", "echo json_encode(get_loaded_extensions());"], env=environment
        ), "Module inventory"))
        if expected - actual:
            raise RuntimeError(f"Missing static extensions: {sorted(expected - actual)}")
    probe = """
    $db = new SQLite3(':memory:');
    $pdo = new PDO('sqlite::memory:');
    $zip = new ZipArchive();
    $ok = $db->querySingle('SELECT 42') === 42
        && $pdo->query('SELECT 42')->fetchColumn() == 42
        && (string) simplexml_load_string('<v>42</v>') === '42'
        && mb_strlen('日本語', 'UTF-8') === 3
        && gzdecode(gzencode('ok')) === 'ok'
        && strlen(openssl_random_pseudo_bytes(16)) === 16
        && curl_version()['version'] !== ''
        && function_exists('imagecreatetruecolor')
        && function_exists('mb_ereg')
        && gmp_strval(gmp_add(40, 2)) === '42';
    if (!$ok) { throw new RuntimeException('Extension probe failed'); }
    echo json_encode(['sapi' => PHP_SAPI, 'version' => PHP_VERSION]);
    """
    probe = (
        "$required = json_decode(" + json.dumps(json.dumps(sorted(expected))) + ", true);"
        "foreach ($required as $extension) {"
        "if (!extension_loaded($extension)) { throw new RuntimeException('Missing: '.$extension); }"
        "}\n" + probe
    )
    if args.system_ca:
        probe = """
        $locations = openssl_get_cert_locations();
        if ($locations['default_cert_file'] !== '/etc/ssl/cert.pem'
            || !is_readable('/etc/ssl/cert.pem')) {
            throw new RuntimeException('Runtime does not use the macOS system CA bundle');
        }
        """ + probe
    if args.features:
        probe = """
        $gd = gd_info();
        foreach (['JPEG Support', 'PNG Support', 'WebP Support', 'AVIF Support',
                  'JIS-mapped Japanese Font Support'] as $feature) {
            if (empty($gd[$feature])) { throw new RuntimeException('Missing GD feature: '.$feature); }
        }
        if ($gd['FreeType Support'] || READLINE_LIB !== 'libedit') {
            throw new RuntimeException('Unexpected GD/readline feature configuration');
        }
        if (defined('PCRE_JIT_SUPPORT') && PCRE_JIT_SUPPORT) {
            throw new RuntimeException('PCRE JIT requires executable-memory signing exceptions');
        }
        if (preg_match('/^\\\\p{L}+$/u', '日本語') !== 1) {
            throw new RuntimeException('Unicode regular expression failed');
        }
        $image = imagecreatetruecolor(2, 2);
        foreach (['imagepng', 'imagejpeg', 'imagewebp', 'imageavif'] as $encoder) {
            ob_start();
            $ok = $encoder($image);
            $encoded = ob_get_clean();
            if (!$ok || $encoded === '') { throw new RuntimeException($encoder.' failed'); }
            $decoded = imagecreatefromstring($encoded);
            if ($decoded === false || imagesx($decoded) !== 2 || imagesy($decoded) !== 2) {
                throw new RuntimeException($encoder.' round trip failed');
            }
        }
        """ + probe
    result = decode_json(subprocess.check_output(cli + ["-r", probe], env=environment), "CLI probe")
    if result != {"sapi": "cli", "version": version}:
        raise RuntimeError(f"Unexpected CLI response: {result}")
    if args.tls:
        subprocess.run(cli + ["-r", """
        $curl = curl_init('https://www.php.net/');
        curl_setopt_array($curl, [
            CURLOPT_NOBODY => true, CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 30, CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_SSL_VERIFYHOST => 2,
        ]);
        if (curl_exec($curl) === false) { throw new RuntimeException(curl_error($curl)); }
        $socket = stream_socket_client('tls://www.php.net:443', $errno, $message, 30);
        if ($socket === false) { throw new RuntimeException($message, $errno); }
        fclose($socket);
        """], env=environment, check=True)
        reject_untrusted_tls(cli, environment)
    # Short socket path avoids Darwin's 104-byte sockaddr_un limit.
    with tempfile.TemporaryDirectory(prefix="php-test-", dir="/tmp") as temporary:
        root = Path(temporary)
        script = root / "probe.php"
        script.write_text("<?php\n" + probe)
        if args.transport == "tcp":
            with socket.socket() as reservation:
                reservation.bind(("127.0.0.1", 0))
                address = reservation.getsockname()
            binding = f"{address[0]}:{address[1]}"
        else:
            address = str(root / "fcgi.sock")
            binding = address
        log = root / "stderr.log"
        with log.open("w+") as stderr:
            process = subprocess.Popen(
                prefix + [str(directory / "php-cgi"), "-n", "-b", binding],
                env=environment, stdout=stderr, stderr=stderr,
            )
            try:
                deadline = time.monotonic() + 15
                while True:
                    if process.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError(f"FastCGI did not start: {log.read_text()}")
                    if args.transport == "tcp":
                        with socket.socket() as connection:
                            connection.settimeout(0.2)
                            ready = connection.connect_ex(address) == 0
                    else:
                        ready = Path(address).exists()
                    if ready:
                        break
                    time.sleep(0.05)
                params = {
                    "SCRIPT_FILENAME": str(script), "SCRIPT_NAME": "/probe.php",
                    "REQUEST_METHOD": "GET", "SERVER_PROTOCOL": "HTTP/1.1",
                    "GATEWAY_INTERFACE": "CGI/1.1", "REDIRECT_STATUS": "200",
                }
                for _ in range(2):
                    headers, body = request(address, params)
                    if headers.get("Status", "200 OK") != "200 OK":
                        raise RuntimeError(f"FastCGI HTTP error: {headers}")
                    if decode_json(body, "FastCGI probe") != {"sapi": "cgi-fcgi", "version": version}:
                        raise RuntimeError(f"Unexpected FastCGI response: {body!r}")
                bridge = Path(__file__).resolve().parents[2] / "php/Resources/php/_4D_Execute_PHP.php"
                headers, body = request(address, {
                    **params, "SCRIPT_FILENAME": str(bridge),
                    "_4D_IsCalledFrom4D": "yes", "_4D_ScriptPath": "php_command",
                    "_4D_FunctionName": "strtoupper", "_4D_FunctionParams": '["hello"]',
                })
                if headers.get("X-4D-FunctionResult") != base64.b64encode(b"HELLO").decode():
                    raise RuntimeError(f"4D bridge failed: {headers}, {body!r}")
            finally:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    print(f"PHP {version}: CLI, extensions, persistent FastCGI, and 4D bridge OK")


if __name__ == "__main__":
    main()
