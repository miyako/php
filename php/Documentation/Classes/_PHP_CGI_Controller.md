# _PHP_CGI_Controller
### Extends `_PHP_Controller` as the controller for the long-running `php-cgi` process.

> _PHP_CGI_Controller.new (CLI : cs.PHP._CLI)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| CLI | cs.PHP._CLI | -> | The owning `_CLI` instance |

## Description

`_PHP_CGI_Controller` is the controller used by [`_PHP_CGI_CLI`](_PHP_CGI_CLI.md) when running the `php-cgi` FastCGI process. It extends [`_PHP_Controller`](_PHP_Controller.md) and overrides all five event callbacks as explicit no-ops.

Because `php-cgi -b` runs as a persistent background process that communicates with 4D via the FastCGI protocol (not via stdout/stderr), no output handling is needed in the controller. 4D's `PHP Execute` command communicates with the process directly over the network.

### Overridden event callbacks

All five callbacks are overridden as no-ops: `onData`, `onDataError`, `onResponse`, `onError`, `onTerminate`.

## See also

- [`_PHP_Controller`](_PHP_Controller.md) — parent class
- [`_PHP_CGI_CLI`](_PHP_CGI_CLI.md) — the CLI class that attaches this controller
- [`PHP_CGI`](PHP_CGI.md) — passes this controller to `_PHP_CGI_CLI`
