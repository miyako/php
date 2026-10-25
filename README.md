![version](https://img.shields.io/badge/version-20%20R5%2B-E23089)
![platform](https://img.shields.io/static/v1?label=platform&message=mac-intel%20|%20mac-arm%20|%20win-64&color=blue)
[![license](https://img.shields.io/github/license/miyako/php)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/php/total)

* the source code of this component is licensed under the [MIT license](https://github.com/miyako/php/blob/master/LICENSE).
* see [php.net](https://www.php.net/license/index.php) for the licensing of **PHP**.

# php

Use PHP as one-shot CLI, FastCGI, or interactive worker process.

## Building PHP for macOS

The [macOS PHP build system](scripts/php-macos/README.md) builds the latest stable
PHP CLI and FastCGI interpreters from source for Apple Silicon and Intel, combines
them into universal binaries, and supports Developer ID signing and Apple
notarization. Third-party dependencies are linked statically; macOS system
libraries remain dynamic.

## Packaging PHP for Windows

The [Windows PHP packaging system](scripts/php-windows/README.md) downloads and
verifies the latest official x64 NTS distribution, configures its DLL extensions
for relocatable 4D workers, records vendor Authenticode status, and packages it
only after native Windows CLI and FastCGI checks succeed.

## Usage

```4d
$CGI:=cs.PHP.PHP_CGI.new(cs.PHP._PHP_CGI_Controller).cgi()

$php:="<?php\n\nfunction sum(int $a, int $b): int {\nreturn $a + $b;\n}\n"

$phpFile:=Folder(fk desktop folder).file("test.php")
$phpFile.setText($php)

var $returnValue : Text
If (PHP Execute($phpFile.platformPath; "sum"; $returnValue; 5; 3))
	ALERT($returnValue)
End if
```

to test CGI mode

```4d
#DECLARE($params : Object)

If (Count parameters=0)
	CALL WORKER(1; Current method name; {})
Else 
	$form:=cs.PHP.CGI_PHPForm.new()
End if
```

to test interactive

```4d
#DECLARE($params : Object)

If (Count parameters=0)
	CALL WORKER(1; Current method name; {})
Else 
	$form:=cs.PHP.Interactive_PHPForm.new()
End if
```

to test one-shot

```4d
#DECLARE($params : Object)

If (Count parameters=0)
	CALL WORKER(1; Current method name; {})
Else 
	$form:=cs.PHP.Run_PHPForm.new()
End if 
```
