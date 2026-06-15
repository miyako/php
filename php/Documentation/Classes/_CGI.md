# _CGI
### Abstract shared singleton base class for managing a long-running CGI/FastCGI process in a named worker.

> _CGI.new (name : Text)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| name | Text | -> | Worker name used to identify this singleton's named worker process |

## Description

`_CGI` is a **shared singleton** base class. It manages the lifecycle of a `_CLI` instance that must live inside a dedicated named 4D worker — necessary because a `4D.SystemWorker` cannot be shared across process boundaries.

`start` and `stop` synchronise across process boundaries using `4D.Signal`: the caller blocks until the named worker has completed the requested operation.

### Properties

| Property | Type | Description |
| --- | --- | --- |
| name | Text | Worker name (read-only) |
| isRunning | Boolean | `True` when the CGI process is active (read-only) |

### Methods

#### start (function : 4D.Function; …) 

Signals the named worker to start the CGI process. Blocks the caller until the worker confirms startup via a signal.

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| function | 4D.Function | -> | Factory function called inside the named worker to create the `_CLI` instance |
| … | Variant | -> | Additional parameters forwarded to `function` |

The `_CLI` instance created by `function` is stored in the process variable `__CLI__` inside the named worker (because a `4D.SystemWorker` cannot be cloned as a shared object). `setRunning(True)` is called and the signal is triggered when done.

#### stop ()

Signals the named worker to terminate the running `_CLI` worker. Blocks until confirmed. After stopping, `KILL WORKER` is called to end the named worker process itself.

#### setRunning (isRunning : Boolean) *(shared)*

Updates the `isRunning` flag. Must be called inside a `Use`/`End use` block (handled automatically by `start` and `stop`).

#### expand (in : Object) → Object

Re-creates a `4D.File` or `4D.Folder` from its platform path. Inherited by subclasses.

#### quote (in : Text) → Text

Wraps a string in double quotes.

## See also

- [`PHP_CGI`](PHP_CGI.md) — extends `_CGI` for the `php-cgi` FastCGI process
- [`_PHP_CGI_CLI`](_PHP_CGI_CLI.md) — the `_CLI` subclass instantiated inside the named worker
