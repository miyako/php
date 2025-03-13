property utilityFile : 4D:C1709.File

Class extends _CGI

shared singleton Class constructor($controller : 4D:C1709.Class; $ini : 4D:C1709.File)
	
	Super:C1705("PHP")
	
	This:C1470.controller:=$controller
	
	If (Is Windows:C1573) && ($ini=Null:C1517)
		$ini:=File:C1566("/RESOURCES/php/php.ini")
	End if 
	
	If (OB Instance of:C1731($ini; 4D:C1709.File))
		If ($ini.exists)
			This:C1470.ini:=This:C1470.expand($ini)
		End if 
	End if 
	
	var $temporaryFolder : 4D:C1709.Folder
	$temporaryFolder:=Folder:C1567(Temporary folder:C486; fk platform path:K87:2).folder(Generate UUID:C1066)
	$temporaryFolder.create()
	
	var $utilityFile : 4D:C1709.File
	$utilityFile:=File:C1566("/RESOURCES/php/_4D_Execute_PHP.php")
	$utilityFile:=This:C1470.expand($utilityFile.copyTo($temporaryFolder))
	
	Use (This:C1470)
		This:C1470._utilityFile:=$utilityFile
	End use 
	
Function get utilityFile()
	
	return This:C1470._utilityFile
	
Function get FULL_PATH_TO_4D_Execute_PHP() : Text
	
	return This:C1470.quote(This:C1470.utilityFile.path)
	
Function _auto_prepend_file()
	
	If (This:C1470.ini#Null:C1517)
		
		var $php : Text
		
		$php:=This:C1470.ini.getText()
		
		ARRAY LONGINT:C221($pos; 0)
		ARRAY LONGINT:C221($len; 0)
		
		If (Match regex:C1019("([;[:Zs:]]*(auto_prepend_file)(\\s*=))"; $php; 1; $pos; $len))
			
			$c:=Substring:C12($php; $pos{2}; $len{2})  //auto_prepend_file
			$c+=" = "
			$c+=This:C1470.FULL_PATH_TO_4D_Execute_PHP
			
			$b:=Substring:C12($php; 1; $pos{1}-1)
			$a:=Substring:C12($php; $pos{1}+$len{1})
			
			This:C1470._setPhpIni($b+$c+$a)
			
		Else 
			//don't prepend file
		End if 
		
	Else 
		This:C1470._setPhpIni("auto_prepend_file = "+This:C1470.FULL_PATH_TO_4D_Execute_PHP)
	End if 
	
Function _cgi($class : 4D:C1709.Class; $ini : 4D:C1709.File)->$controller : cs:C1710._PHP_CGI_CLI
	
	$options:={}
	var $stringValue : Text
	
	$options.address:=(Get database parameter:C643(PHP interpreter IP address:K37:59; $stringValue)) && $stringValue
	$options.port:=Get database parameter:C643(PHP interpreter port:K37:55)
	$options.children:=Get database parameter:C643(_o_PHP number of children:K37:56)
	$options.requests:=Get database parameter:C643(_o_PHP max requests:K37:57)
	
	SET DATABASE PARAMETER:C642(_o_PHP use external interpreter:K37:58; 1)
	
	$controller:=cs:C1710._PHP_CGI_CLI.new($class; $ini).cgi($options)
	
shared Function _setPhpIni($ini : Text)
	
	This:C1470.ini:=This:C1470.expand(File:C1566("/LOGS/php-cgi.ini"))
	This:C1470.ini.setText($ini)
	
Function cgi()->$this : cs:C1710.PHP_CGI
	
	$this:=This:C1470
	
	If (Not:C34(This:C1470.isRunning))
		
		This:C1470._auto_prepend_file()
		
		This:C1470.start(This:C1470._cgi; This:C1470.controller; This:C1470.ini)
		
	End if 
	
Function terminate()
	
	If (This:C1470.isRunning)
		
		This:C1470.stop()
		
	End if 