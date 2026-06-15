# _PHPForm
### Extends `_Form` with shared UI state and input/history management for PHP REPL forms.

> _PHPForm.new ()

No parameters.

## Description

`_PHPForm` is the common form controller base class for all three PHP form variants ([`Run_PHPForm`](Run_PHPForm.md), [`Interactive_PHPForm`](Interactive_PHPForm.md), [`CGI_PHPForm`](CGI_PHPForm.md)). It manages the form's output list, input field, and command history, and provides a context menu for clearing output.

All methods operate on `Form` object properties: `Form.output`, `Form.input`, `Form.history`, `Form.cursor`, and `Form.PHP`.

### Methods

#### clearOutput () → Form

Resets `Form.output` to an empty collection.

#### clearInput () → Form

Resets `Form.input` to an empty string.

#### clearHistory () → Form

Resets `Form.history` to `[""]` and selects position 0.

#### push ($line : Text)

Appends a line to `Form.output`, clears `Form.input`, and scrolls the Output list box to the last row.

#### rewind () → Form

Moves the history cursor back one step if not already at the beginning.

#### forward () → Form

Moves the history cursor forward one step if not already at the end.

#### selectHistory ($i : Integer)

Sets `Form.cursor` to `$i`, selects the corresponding row in the History list box, and copies `Form.history[$i]` into `Form.input`.

#### popupMenu ()

On contextual click, shows a pop-up menu with a "クリア" (Clear) item. If selected, calls `clearOutput()`.

## See also

- [`_Form`](_Form.md) — parent class
- [`Run_PHPForm`](Run_PHPForm.md) — one-shot execution form
- [`Interactive_PHPForm`](Interactive_PHPForm.md) — interactive REPL form
- [`CGI_PHPForm`](CGI_PHPForm.md) — CGI mode form
