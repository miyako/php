Class extends _PHP_Controller

Class constructor($CLI : cs:C1710._CLI)
	
	Super:C1705($CLI)
	
Function onData($worker : 4D:C1709.SystemWorker; $params : Object)
	
	If (Form:C1466#Null:C1517) && (OB Instance of:C1731(Form:C1466.push; 4D:C1709.Function))
		If ($worker.dataType="text")
			For each ($line; Split string:C1554($params.data; "\n"; sk ignore empty strings:K86:1))
				If ($line="php > ")
					break
				End if 
				Form:C1466.push($line)
			End for each 
		End if 
	End if 
	
Function onDataError($worker : 4D:C1709.SystemWorker; $params : Object)
	
Function onResponse($worker : 4D:C1709.SystemWorker; $params : Object)
	
Function onError($worker : 4D:C1709.SystemWorker; $params : Object)
	
Function onTerminate($worker : 4D:C1709.SystemWorker; $params : Object)
	