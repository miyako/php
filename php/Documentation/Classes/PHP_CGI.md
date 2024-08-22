# PHP_CGI : _CGI

`PHP_CGI` is a subclass of `_CGI` to control `php-cgi`, the FastCGI version of PHP. Use this class to reactivate the native command `PHP Execute` in v20 R3 or later.

## .new() 

**.new**($controller : 4D.Class; $ini : 4D.File) : cs.PHP_CGI

Pass a subclass of `_CLI_Controller` and a php.ini file. 

Properties:

|Property|Type|Description|
|:-|:-|:-|
|utilityFile|4D.File|the *_4D_Execute_PHP.php* file in /RESOURCES/ (read-only)|
|FULL_PATH_TO_4D_Execute_PHP|Text|the quoted platform path to This.utilityFile (read-only)|

## .cgi()

**.cgi**() : cs.PHP_CGI

Launch the `php-cgi` program as an external PHP interpreter in a worker using `_PHP_CGI_CLI`. The `_PHP_CGI_CLI` instance is stored in a process variable in the worker's execution context. The path to `This.utilityFile` is automatically added to the php.ini file.

## .terminate()

**.terminate**()

Terminate the `php-cgi` program.  