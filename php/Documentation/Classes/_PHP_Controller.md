# _PHP_Controller
### Extends `_CLI_Controller` to capture stdout and stderr from a `php` execution.

> _PHP_Controller.new (CLI : cs.PHP._CLI)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| CLI | cs.PHP._CLI | -> | The owning `_CLI` instance |

## Description

`_PHP_Controller` is the default controller used by [`PHP`](PHP.md). It inherits all command-queue and worker-management behaviour from [`_CLI_Controller`](_CLI_Controller.md) and overrides `onResponse` to store the worker's output on the owning `PHP` instance.

`onData`, `onDataError`, `onError`, and `onTerminate` are declared as no-ops (overridable in subclasses).

### Overridden event callbacks

#### onResponse ($worker : 4D.SystemWorker; $params : Object)

When the worker finishes, writes `worker.response` to `instance.data` and `worker.responseError` to `instance.error`.

After a synchronous `PHP.run()` call, read results from the controller:

```4d
$PHP.run("echo 42;")
ALERT($PHP.controller.instance.data)   // "42"
ALERT($PHP.controller.instance.error)  // stderr if any
```

## See also

- [`_CLI_Controller`](_CLI_Controller.md) — parent class
- [`PHP`](PHP.md) — attaches this controller by default
- [`_PHPUI_Controller`](_PHPUI_Controller.md) — subclass for interactive form output
- [`_PHP_CGI_Controller`](_PHP_CGI_Controller.md) — subclass for `php-cgi` (all callbacks are no-ops)
