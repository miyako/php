# _CLI
### Abstract base class for wrapping a platform-native CLI executable.

> _CLI.new (executableName : Text; controller : 4D.Class)

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| executableName | Text | -> | Base name of the executable (without `.exe` on Windows) |
| controller | 4D.Class | -> | Controller class to attach (default: `cs.PHP._CLI_Controller`) |

## Description

`_CLI` resolves the platform-specific path to a bundled executable and attaches a controller that manages the underlying `4D.SystemWorker`. It is extended by [`PHP`](PHP.md) and [`_PHP_CGI_CLI`](_PHP_CGI_CLI.md) and should not be instantiated directly.

### Resolution strategy

The constructor looks for the executable under `/RESOURCES/bin/{platform}/`. If found, the full path is stored and `chmod +x` is applied on macOS. If not found, the executable name alone is stored and resolution is delegated to `$PATH` at runtime.

Platform identifiers:

| Platform | Value |
| --- | --- |
| macOS | `macOS` |
| Windows | `Windows` |

Note: this version of `_CLI` does not include ARM detection on Windows. The `currentDirectory` for workers defaults to the system temporary folder rather than the executable's directory.

### Properties (read-only)

| Property | Type | Description |
| --- | --- | --- |
| name | Text | Class name |
| EOL | Text | `\n` on macOS, `\r\n` on Windows |
| executableName | Text | Resolved executable file name |
| platform | Text | Platform string (`"macOS"` or `"Windows"`) |
| currentDirectory | 4D.Folder | Folder containing the executable |
| executablePath | Text | Full path (or bare name) of the executable |
| executableFile | 4D.File | `4D.File` reference to the executable |
| controller | cs.PHP._CLI_Controller | Attached controller instance |

### Methods

#### escape (in : Text) → Text

Shell-escapes a string for the current platform.

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| in | Text | -> | Raw string to escape |
| Result | Text | <- | Shell-safe string |

On macOS/zsh prefixes each shell metacharacter with `\`. On Windows/cmd.exe wraps in double quotes when metacharacters are present.

#### expand (in : Object) → Object

Re-creates a `4D.File` or `4D.Folder` from its platform path.

#### quote (in : Text) → Text

Wraps a string in double quotes unconditionally.

## See also

- [`_CLI_Controller`](_CLI_Controller.md) — manages `4D.SystemWorker` execution
- [`PHP`](PHP.md) — extends `_CLI` to wrap the `php` executable
- [`_PHP_CGI_CLI`](_PHP_CGI_CLI.md) — extends `_CLI` to wrap `php-cgi`
