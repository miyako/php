Class extends _PHPForm

Class constructor
	
	Super:C1705()
	
	$window:=Open form window:C675("PHP")
	DIALOG:C40("PHP"; This:C1470; *)
	
Function onLoad()
	
	If (Is Windows:C1573)
		$ini:=File:C1566("/RESOURCES/php/php.ini")
	End if 
	
	Form:C1466.PHP:=cs:C1710.PHP.new(cs:C1710._PHPUI_Controller; $ini)
	
	Form:C1466.clearOutput().clearInput().clearHistory()
	
	Form:C1466.PHP.interactive()
	
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
	
	Form:C1466.PHP.controller.worker.postMessage($input+"\r\n")
	
	return Form:C1466