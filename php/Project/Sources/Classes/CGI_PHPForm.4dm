Class extends _PHPForm

Class constructor
	
	Super:C1705()
	
	$window:=Open form window:C675("PHP")
	DIALOG:C40("PHP"; This:C1470; *)
	
Function onLoad()
	
	If (Is Windows:C1573)
		$ini:=File:C1566("/RESOURCES/php/php.ini")
	End if 
	
	Form:C1466.PHP:=cs:C1710.PHP_CGI.new(cs:C1710._PHP_CGI_Controller; $ini)
	
	Form:C1466.clearOutput().clearInput().clearHistory()
	
	Form:C1466.PHP.cgi()
	
Function onUnload()
	
	Form:C1466.PHP.terminate()
	
Function post()
	
	If (OBJECT Get name:C1087(Object with focus:K67:3)="Input")
		$input:=Get edited text:C655
	Else 
		$input:=Form:C1466.input
	End if 
	
	Form:C1466.history.insert(-1; $input)
	Form:C1466.selectHistory(Form:C1466.history.length-1)
	
	$f:=Folder:C1567(Temporary folder:C486; fk platform path:K87:2).file(Generate UUID:C1066+".php")
	$f.setText("<?php\n"+$input)
	
	$success:=PHP Execute:C1058($f.platformPath; ""; $returnValue)
	
	If ($success)
		var $stdOut : Text
		PHP GET FULL RESPONSE:C1061($stdOut)
		For each ($line; Split string:C1554($stdOut; "\n"; sk ignore empty strings:K86:1))
			If ($line="php > ")
				break
			End if 
			Form:C1466.push($line)
		End for each 
	End if 
	
	return Form:C1466