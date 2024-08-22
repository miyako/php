# _PHP_CGI_CLI : _CLI

`_PHP_CGI_CLI` is a subclass of `_CLI` to launch `php-cgi`, the FastCGI version of PHP. 

## .new() 

**.new**($controller : 4D.Class; $ini : 4D.File) : cs._PHP_CGI_CLI

Pass a subclass of `_CLI_Controller` and a php.ini file. 

Properties:

|Property|Type|Description|
|:-|:-|:-|
|utilityFile|4D.File|the *_4D_Execute_PHP.php* file in /RESOURCES/ (read-only)|
|FULL_PATH_TO_4D_Execute_PHP|Text|the quoted platform path to This.utilityFile (read-only)|

## .cgi() 

**.cgi**($options : Object) : cs._PHP_CGI_CLI

Launch `php-cgi` with the command line arguments `-b` (binding) and `-c` or `-n`.

Options:

|Property|Type|Description|
|:-|:-|:-|
|address|Text|normally database parameter `PHP interpreter IP address`|
|port|Number|normally database parameter `PHP interpreter IP address`|
|children|Number|normally database parameter `_o_PHP number of children`|
|requests|Number|normally database parameter `_o_PHP max requests`|