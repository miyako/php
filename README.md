![version](https://img.shields.io/badge/version-20%20R5%2B-E23089)
![platform](https://img.shields.io/static/v1?label=platform&message=mac-intel%20|%20mac-arm%20|%20win-64&color=blue)
[![license](https://img.shields.io/github/license/miyako/php)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/php/total)

### Licensing

* the source code of this component is licensed under the [MIT license](https://github.com/miyako/php/blob/master/LICENSE).
* see [php.net](https://www.php.net/license/index.php) for the licensing of **PHP**.

# php

## dependencies.json

```json
{
	"dependencies": {
		"php": {
			"github": "miyako/php",
			"version": "*"
		}
	}
}
```

Based on [miyako/4d-class-php](https://github.com/miyako/4d-class-php).

The CGI class has been refactored as a Shared Singleton.

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
