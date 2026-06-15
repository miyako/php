# Interactive_PHPForm
### Form controller that maintains a persistent `php -a` interactive session.

> Interactive_PHPForm.new ()

No parameters. Opens the `"PHP"` form window immediately on construction.

## Description

`cs.PHP.Interactive_PHPForm` extends [`_PHPForm`](_PHPForm.md) and implements the interactive REPL pattern: a single `PHP` instance is started in interactive mode (`php -a`) on form load and kept alive until the form closes. Each submission sends the input directly to the worker's stdin; output is delivered asynchronously by `_PHPUI_Controller.onData`.

Invoke from a named worker:

```4d
#DECLARE($params : Object)
If (Count parameters=0)
    CALL WORKER(1; Current method name; {})
Else 
    $form:=cs.PHP.Interactive_PHPForm.new()
End if
```

### Methods

#### onLoad ()

Creates `Form.PHP` as `PHP.new(cs.PHP._PHPUI_Controller)`, clears the form state, and calls `Form.PHP.interactive()` to start `php -a`.

On Windows a `php.ini` from `/RESOURCES/php/php.ini` is loaded automatically.

#### onUnload ()

Calls `Form.PHP.terminate()` to stop the interactive worker when the form closes.

#### post () → Form

Reads input, appends to history, and posts `input + "\r\n"` to `Form.PHP.controller.worker`. The `_PHPUI_Controller` handles incoming stdout and calls `Form.push` automatically.

## See also

- [`_PHPForm`](_PHPForm.md) — parent class
- [`PHP`](PHP.md) — `interactive()` is called on load
- [`_PHPUI_Controller`](_PHPUI_Controller.md) — routes stdout to `Form.push`
