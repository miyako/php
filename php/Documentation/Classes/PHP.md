# PHP : _CLI

`PHP` is a subclass of `_CLI` to execute `php` in one-shot or interactive mode. 

## .new() 

**.new**($controller : 4D.Class; $ini : 4D.File) : cs.PHP

Pass a subclass of `_CLI_Controller` and a php.ini file. 

Properties:

|Property|Type|Description|
|:-|:-|:-|
|utilityFile|4D.File|the *_4D_Execute_PHP.php* file in /RESOURCES/ (read-only)|
|FULL_PATH_TO_4D_Execute_PHP|Text|the quoted platform path to This.utilityFile (read-only)|

## .interactive()

**.interactive**($php : Variant) : cs.PHP

Execute `php` with the command line arguments `-a` and `-c` or `-n`.

## .run()

**.run**($php : Variant) : cs.PHP

Execute `php` with the command line arguments `-r` or `-f` and `-c` or `-n`.

Pass a `4D.File` to execute a script. Else pass text to execute code.

## .terminate()

**.terminate**()

Terminate the `php` program.  
