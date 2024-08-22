Class extends _PHPForm

Class constructor
	
	Super:C1705()
	
	$window:=Open form window:C675("PHP")
	DIALOG:C40("PHP"; This:C1470; *)
	
Function onLoad()
	
	Form:C1466.clearOutput().clearInput().clearHistory()
	
Function post()
	
	If (OBJECT Get name:C1087(Object with focus:K67:3)="Input")
		$input:=Get edited text:C655
	Else 
		$input:=Form:C1466.input
	End if 
	
	Form:C1466.history.insert(-1; $input)
	Form:C1466.selectHistory(Form:C1466.history.length-1)
	
	If (Is Windows:C1573)
		$ini:=File:C1566("/RESOURCES/php/php.ini")
	End if 
	
	Form:C1466.PHP:=cs:C1710.PHP.new(cs:C1710._PHP_Controller; $ini)
	
	$stdOut:=Form:C1466.PHP.run($input).data
	
	For each ($line; Split string:C1554($stdOut; "\n"; sk ignore empty strings:K86:1))
		If ($line="php > ")
			break
		End if 
		Form:C1466.push($line)
	End for each 
	
	return Form:C1466