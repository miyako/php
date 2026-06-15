# _Form
### Abstract base class for 4D form controllers.

> _Form.new ()

No parameters.

## Description

`_Form` is the root form controller class in the `cs.PHP` namespace. It declares stub lifecycle methods (`onLoad`, `onUnload`) that are called by 4D when the form opens and closes. It is extended by [`_PHPForm`](_PHPForm.md) and should not be instantiated directly.

### Methods

#### onLoad ()

Called when the form opens. No-op in the base class; override in subclasses.

#### onUnload ()

Called when the form closes. No-op in the base class; override in subclasses.

## See also

- [`_PHPForm`](_PHPForm.md) — extends `_Form` with PHP-specific UI logic
