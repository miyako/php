# Run_PHPForm
### Form controller that runs a PHP snippet in one-shot mode on each submission.

> Run_PHPForm.new ()

No parameters. Opens the `"PHP"` form window immediately on construction.

## Description

`cs.PHP.Run_PHPForm` extends [`_PHPForm`](_PHPForm.md) and implements the one-shot execution pattern: each time the user submits input, a new `PHP` instance is created, `run()` is called synchronously, and the output is pushed to the form's list box. No persistent PHP process is kept between submissions.

Invoke from a named worker:

```4d
#DECLARE($params : Object)
If (Count parameters=0)
    CALL WORKER(1; Current method name; {})
Else 
    $form:=cs.PHP.Run_PHPForm.new()
End if
```

### Methods

#### onLoad ()

Clears the form's output, input, and history.

#### post () → Form

Reads the current input (from the focused `Input` object or `Form.input`), appends it to history, creates a new `PHP` instance, calls `run($input)`, and pushes each line of stdout to the form output.

On Windows a `php.ini` from `/RESOURCES/php/php.ini` is loaded automatically.

## See also

- [`_PHPForm`](_PHPForm.md) — parent class
- [`PHP`](PHP.md) — used for each one-shot execution
- [`_PHP_Controller`](_PHP_Controller.md) — controller used by `PHP`
