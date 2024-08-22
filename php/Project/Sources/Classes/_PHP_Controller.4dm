Class extends _CLI_Controller

Class constructor($CLI : cs:C1710._CLI)
	
	Super:C1705($CLI)
	
Function onData($worker : 4D:C1709.SystemWorker; $params : Object)
	
Function onDataError($worker : 4D:C1709.SystemWorker; $params : Object)
	
Function onResponse($worker : 4D:C1709.SystemWorker; $params : Object)
	
	This:C1470.instance.data:=$worker.response
	
Function onError($worker : 4D:C1709.SystemWorker; $params : Object)
	
Function onTerminate($worker : 4D:C1709.SystemWorker; $params : Object)
	