Class constructor($name : Text)
	
	This:C1470._name:=$name
	This:C1470._isRunning:=False:C215
	//%W-520.19
	var __CLI__ : Object
	//%W+520.19
Function get name()
	
	return This:C1470._name
	
Function get isRunning : Boolean
	
	return This:C1470._isRunning
	
Function setRunning($isRunning : Boolean)
	
	This:C1470._isRunning:=$isRunning
	
Function expand($in : Object)->$out : Object
	
	$out:=OB Class:C1730($in).new($in.platformPath; fk platform path:K87:2)
	
Function quote($in : Text)->$out : Text
	
	$out:="\""+$in+"\""
	
Function start($function : 4D:C1709.Function)
	
	C_VARIANT:C1683(${2})
	
	$signal:=New signal:C1641
	
	CALL WORKER:C1389(This:C1470.name; This:C1470._start; This:C1470; $function; $signal; Copy parameters:C1790(2))
	
	$signal.wait()
	
Function _start($that : cs:C1710._CGI; $function : 4D:C1709.Function; $signal : 4D:C1709.Signal; $params : Collection)
	
	var $CLI : cs:C1710._CLI
	
	$CLI:=$function.apply($that; $params)
	
	//can't use OB Copy because a SystemWorker can't be cloned as a shared object
	
	__CLI__:=$CLI
	
	$that.setRunning(True:C214)
	
	$signal.trigger()
	
Function stop()
	
	$signal:=New signal:C1641
	
	CALL WORKER:C1389(This:C1470.name; This:C1470._stop; This:C1470; $signal)
	
	$signal.wait()
	
Function _stop($that : cs:C1710._CGI; $signal : 4D:C1709.Signal)
	
	var $CLI : cs:C1710._CLI
	
	$CLI:=__CLI__
	
	If ($CLI.controller.worker#Null:C1517)
		
		$CLI.controller.worker.terminate()
		
	End if 
	
	CLEAR VARIABLE:C89(__CLI__)
	
	$that.setRunning(False:C215)
	
	$signal.trigger()
	
	KILL WORKER:C1390