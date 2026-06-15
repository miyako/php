# _PHPUI_Controller
### Extends `_PHP_Controller` to route interactive PHP stdout directly to the active form.

> _PHPUI_Controller.new (CLI : cs.PHP._CLI)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| CLI | cs.PHP._CLI | -> | The owning `_CLI` instance |

## Description

`_PHPUI_Controller` is used with [`PHP.interactive()`](PHP.md) when running inside a 4D form. It overrides `onData` to parse each line of stdout and call `Form.push($line)`, filtering out the `php > ` prompt that the interactive shell emits.

All other callbacks (`onDataError`, `onResponse`, `onError`, `onTerminate`) are declared as no-ops.

### Overridden event callbacks

#### onData ($worker : 4D.SystemWorker; $params : Object)

When `Form` is present and has a `push` method, splits `$params.data` on `\n` and calls `Form.push` for each non-empty line, stopping if a line equals `"php > "` (the interactive shell prompt).

## Examples

Pass `_PHPUI_Controller` to `PHP.new` when starting an interactive session from a form:

```4d
Form.PHP:=cs.PHP.PHP.new(cs.PHP._PHPUI_Controller; Null)
Form.PHP.interactive()

// later, send input from the form:
Form.PHP.controller.worker.postMessage("echo 'hello';\r\n")
// Form.push is called automatically with the response
```

## See also

- [`_PHP_Controller`](_PHP_Controller.md) — parent class
- [`PHP`](PHP.md) — `interactive()` uses this controller
- [`Interactive_PHPForm`](Interactive_PHPForm.md) — the form class that uses this controller
