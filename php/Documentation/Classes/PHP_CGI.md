# PHP_CGI
### A shared singleton that manages the `php-cgi` FastCGI process for use with 4D's `PHP Execute`.

> PHP_CGI.new (controller : 4D.Class; ini : 4D.File)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| controller | 4D.Class | -> | Controller class to use for the `php-cgi` worker |
| ini | 4D.File | -> | Optional `php.ini` file; on Windows defaults to `/RESOURCES/php/php.ini` if `Null` |

## Description

`cs.PHP.PHP_CGI` is a **shared singleton** that extends [`_CGI`](_CGI.md). One instance is shared across all contexts in the application. It manages the lifetime of the `php-cgi` FastCGI process that 4D's built-in `PHP Execute` command communicates with.

On construction the class:

1. Copies `/RESOURCES/php/_4D_Execute_PHP.php` to a fresh temporary folder (the utility file that bridges `PHP Execute` to the running process).
2. If no `ini` file is given on Windows, falls back to `/RESOURCES/php/php.ini`.
3. Resolves and stores the `ini` file path.

The singleton is identified by the name `"PHP"` (passed to `_CGI`).

### Properties

| Property | Type | Description |
| --- | --- | --- |
| utilityFile | 4D.File | Copy of `_4D_Execute_PHP.php` in the temporary folder |
| ini | 4D.File | Active `php.ini` file (`Null` if none) |
| isRunning | Boolean | `True` when the `php-cgi` process is active (inherited from `_CGI`) |

### Methods

#### cgi () → cs.PHP.PHP_CGI

Starts the `php-cgi` process if not already running. Returns `This` for chaining.

Internally: patches `auto_prepend_file` in the ini to point to `utilityFile`, reads current database parameters (address, port, children, max requests), sets `_o_PHP use external interpreter` to `1`, then launches the process via `_PHP_CGI_CLI`.

#### terminate ()

Stops the `php-cgi` process if running, then calls `_CGI.stop()`.

## Examples

### Start CGI and use `PHP Execute`

```4d
var $CGI : cs.PHP.PHP_CGI
$CGI:=cs.PHP.PHP_CGI.new(cs.PHP._PHP_CGI_Controller; Null).cgi()

var $phpFile : 4D.File
$phpFile:=Folder(fk desktop folder).file("test.php")
$phpFile.setText("<?php\nfunction sum(int $a, int $b): int {\n    return $a + $b;\n}\n")

var $returnValue : Text
If (PHP Execute($phpFile.platformPath; "sum"; $returnValue; 5; 3))
    ALERT($returnValue)  // "8"
End if
```

### Terminate

```4d
cs.PHP.PHP_CGI.new(Null; Null).terminate()
```

## See also

- [`_CGI`](_CGI.md) — parent shared singleton base class
- [`_PHP_CGI_CLI`](_PHP_CGI_CLI.md) — builds and launches the `php-cgi` command
- [`_PHP_CGI_Controller`](_PHP_CGI_Controller.md) — controller for the `php-cgi` worker
