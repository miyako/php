# _PHP_CGI_CLI
### Extends `_CLI` to build and launch the `php-cgi` FastCGI command.

> _PHP_CGI_CLI.new (controller : 4D.Class; ini : 4D.File)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| controller | 4D.Class | -> | Controller class to attach |
| ini | 4D.File | -> | Optional `php.ini` file |

## Description

`_PHP_CGI_CLI` extends [`_CLI`](_CLI.md) targeting the `php-cgi` executable. It resolves and stores the `ini` path, then provides `cgi()` to assemble the command and start the worker.

It is not used directly by application code; it is instantiated inside the named worker by [`_CGI.start`](_CGI.md) via [`PHP_CGI._cgi`](PHP_CGI.md).

### Methods

#### cgi (options : Object) → cs.PHP._PHP_CGI_CLI

Builds the `php-cgi` command and calls `controller.execute`.

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| options | Object | -> | Object with `address` (Text) and `port` (Integer) from database parameters |
| Result | cs.PHP._PHP_CGI_CLI | <- | `This` |

**Command construction:**

```
php-cgi -b address:port [-c php.ini | -n]
```

- `-b address:port` — bind address and port read from `PHP interpreter IP address` / `PHP interpreter port` database parameters.
- `-c php.ini` — used when an ini file is resolved; otherwise `-n` (no ini).

## See also

- [`_CLI`](_CLI.md) — parent class
- [`PHP_CGI`](PHP_CGI.md) — owns and invokes this class
- [`_PHP_CGI_Controller`](_PHP_CGI_Controller.md) — controller attached to the `php-cgi` worker
