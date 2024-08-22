Class extends _CLI

Class constructor($controller : 4D:C1709.Class; $ini : 4D:C1709.File)
	
	Super:C1705("php-cgi"; $controller)
	
	If (OB Instance of:C1731($ini; 4D:C1709.File))
		If ($ini.exists)
			This:C1470.ini:=This:C1470.expand($ini).path
		End if 
	End if 
	
Function cgi($options : Object)->$this : cs:C1710._PHP_CGI_CLI
	
	$this:=This:C1470
	
	$command:=This:C1470.escape(This:C1470.executablePath)
	$command+=" -b "+$options.address+":"+String:C10($options.port)
	
	If (This:C1470.ini#Null:C1517)
		$command+=" -c "+This:C1470.escape(This:C1470.ini)
	Else 
		$command+=" -n "
	End if 
	
	This:C1470.controller.execute($command)