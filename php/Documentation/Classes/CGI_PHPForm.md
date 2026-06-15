# CGI_PHPForm
### Form controller that runs PHP through the persistent `php-cgi` FastCGI process via `PHP Execute`.

> CGI_PHPForm.new ()

No parameters. Opens the `"PHP"` form window immediately on construction.

## Description

`cs.PHP.CGI_PHPForm` extends [`_PHPForm`](_PHPForm.md) and implements the CGI execution pattern: `PHP_CGI.cgi()` is called on form load to ensure the `php-cgi` FastCGI process is running, and each submission uses 4D's built-in `PHP Execute` command to run code through it.

The `php-cgi` process persists for the lifetime of the form. It is terminated when the form closes.

Invoke from a named worker:

```4d
#DECLARE($params : Object)
If (Count parameters=0)
    CALL WORKER(1; Current method name; {})
Else 
    $form:=cs.PHP.CGI_PHPForm.new()
End if
```

### Methods

#### onLoad ()

Creates `Form.PHP` as `PHP_CGI.new(cs.PHP._PHP_CGI_Controller; $ini)` and calls `Form.PHP.cgi()` to start the FastCGI process. On Windows a `php.ini` from `/RESOURCES/php/php.ini` is loaded automatically.

#### onUnload ()

Calls `Form.PHP.terminate()` to stop the `php-cgi` process.

#### post () → Form

Reads input, appends to history, writes it to a temporary `.php` file (prefixed with `<?php\n`), and calls `PHP Execute` on that file. Parses the full response via `PHP GET FULL RESPONSE`, filters out the `php > ` prompt, and pushes each output line to the form.

## See also

- [`_PHPForm`](_PHPForm.md) — parent class
- [`PHP_CGI`](PHP_CGI.md) — manages the `php-cgi` process
- [`_PHP_CGI_Controller`](_PHP_CGI_Controller.md) — controller for the `php-cgi` worker
