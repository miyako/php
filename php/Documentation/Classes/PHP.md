# PHP
### Wraps the `php` CLI to run PHP code in one-shot or interactive mode via `4D.SystemWorker`.

> PHP.new (controller : 4D.Class; ini : 4D.File)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| controller | 4D.Class | -> | Controller class to attach (default: `cs.PHP._PHP_Controller`) |
| ini | 4D.File | -> | Optional `php.ini` configuration file; required on Windows when the system PHP has no default ini |

## Description

`cs.PHP.PHP` extends [`_CLI`](_CLI.md) and wraps the `php` executable. It supports two execution modes:

- **One-shot** (`run`) — executes a PHP code string or file and returns immediately.
- **Interactive** (`interactive`) — starts `php -a` as a persistent worker; subsequent input is sent via `worker.postMessage`.

On Windows, passing a `php.ini` file is recommended. On macOS the system PHP is used without an ini file unless one is supplied.

### Properties

| Property | Type | Description |
| --- | --- | --- |
| ini | Text | Platform path to the active `php.ini` file (`Null` if none) |
| worker | 4D.SystemWorker | The currently active worker (read-only, from controller) |
| controller | cs.PHP._PHP_Controller | The attached controller instance (read-only) |

### Methods

#### run (php : Text \| 4D.File) → cs.PHP.PHP

Executes PHP in one-shot mode and blocks until the worker finishes.

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| php | Text | -> | PHP code string; executed via `php -r` |
| php | 4D.File | -> | PHP file; executed via `php -f` |
| Result | cs.PHP.PHP | <- | `This` — call `.data` and `.error` on the controller for output |

After the worker terminates, `controller.instance.data` contains stdout and `controller.instance.error` contains stderr (set by `_PHP_Controller.onResponse`).

#### interactive () → cs.PHP.PHP

Starts `php -a` (interactive mode) as a persistent worker. Input is sent line by line via `controller.worker.postMessage`.

| Result | Type | Description |
| --- | --- | --- |
| Result | cs.PHP.PHP | <- | `This` |

Use `_PHPUI_Controller` when running in interactive mode from a form, so stdout is routed to `Form.push` automatically.

#### terminate ()

Delegates to `controller.terminate()`.

## Examples

### One-shot from string

```4d
var $PHP : cs.PHP.PHP
If (Is Windows)
    $ini:=File("/RESOURCES/php/php.ini")
End if
$PHP:=cs.PHP.PHP.new(cs.PHP._PHP_Controller; $ini)
$PHP.run("echo 'Hello, World!';")
ALERT($PHP.controller.instance.data)
```

### One-shot from file

```4d
$phpFile:=Folder(fk desktop folder).file("test.php")
$PHP:=cs.PHP.PHP.new(Null; Null)
$PHP.run($phpFile)
ALERT($PHP.controller.instance.data)
```

### Interactive (from a worker)

```4d
var $PHP : cs.PHP.PHP
$PHP:=cs.PHP.PHP.new(cs.PHP._PHPUI_Controller; Null)
$PHP.interactive()
// later, send input:
$PHP.controller.worker.postMessage("echo 42;\r\n")
```

### Enable CGI mode (for `PHP Execute`)

```4d
$CGI:=cs.PHP.PHP_CGI.new(cs.PHP._PHP_CGI_Controller; Null).cgi()
// now PHP Execute uses the local php-cgi process
var $returnValue : Text
If (PHP Execute($phpFile.platformPath; "sum"; $returnValue; 5; 3))
    ALERT($returnValue)
End if
```

## See also

- [`_PHP_Controller`](_PHP_Controller.md) — default controller; stores stdout/stderr on response
- [`_PHPUI_Controller`](_PHPUI_Controller.md) — controller for interactive forms; routes stdout to `Form.push`
- [`PHP_CGI`](PHP_CGI.md) — manages the `php-cgi` FastCGI process for use with `PHP Execute`
- [`_CLI`](_CLI.md) — parent class
