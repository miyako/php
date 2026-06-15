# _CLI_Controller
### Manages a queue of `4D.SystemWorker` commands for a `_CLI` instance.

> _CLI_Controller.new (CLI : cs.PHP._CLI)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| CLI | cs.PHP._CLI | -> | The owning `_CLI` instance |

## Description

`_CLI_Controller` serializes an ordered queue of shell commands, executing each one in its own `4D.SystemWorker` and advancing to the next only after the previous worker has terminated.

Note: this version of `_CLI_Controller` has a simplified `execute` signature compared to other namespaces — it accepts only a `command` argument (no `message` or `context` parameters). The `currentDirectory` defaults to the system temporary folder rather than the executable's directory.

### Properties

| Property | Type | Description |
| --- | --- | --- |
| dataType | Text | Worker data type (`"text"` by default) |
| encoding | Text | Text encoding (`"UTF-8"` by default) |
| variables | Object | Environment variables injected into each worker |
| timeout | Variant | Worker timeout (`Null` = no timeout) |
| hideWindow | Boolean | Hide the console window on Windows (default: `True`) |
| currentDirectory | 4D.Folder | System temporary folder |
| complete | Boolean | `True` when the command queue has been fully drained |
| worker | 4D.SystemWorker | The currently running worker (`Null` when idle) |
| commands | Collection | Pending command strings |
| instance | cs.PHP._CLI | The owning `_CLI` instance |

### Event callbacks

| Property | Signature | Description |
| --- | --- | --- |
| onData | ($worker; $params) | Fired when the worker emits stdout data |
| onDataError | ($worker; $params) | Fired when the worker emits stderr data |
| onError | ($worker; $params) | Fired on worker error |
| onResponse | ($worker; $params) | Fired when the worker responds (command finished) |
| onTerminate | ($worker; $params) | Fired when the worker terminates |

### Methods

#### execute (command : Text \| Collection)

Enqueues one or more commands and starts execution if no worker is currently running.

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| command | Text \| Collection | -> | Shell command string or a collection of command strings |

#### terminate ()

Aborts the queue, clears all pending commands, terminates the active worker, and resets internal state.

## See also

- [`_CLI`](_CLI.md) — owns and instantiates the controller
- [`_PHP_Controller`](_PHP_Controller.md) — extends `_CLI_Controller` for `php` execution
