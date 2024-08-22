![version](https://img.shields.io/badge/version-20%20R6%2B-E23089)
[![license](https://img.shields.io/github/license/miyako/php)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/php/total)

# php

## dependencies.json

```json
{
	"dependencies": {
		"php": {
			"github": "miyako/php",
			"version": "^0.0.4"
		}
	}
}
```

Based on [miyako/4d-class-php](https://github.com/miyako/4d-class-php).

The CGI class has been refactored as a Shared Singleton.

## Usage

```4d
$CGI:=cs.PHP.PHP_CGI.new(cs.PHP._PHP_CGI_Controller; $ini).cgi()

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
