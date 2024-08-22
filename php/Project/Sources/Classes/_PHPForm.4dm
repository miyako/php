Class extends _Form

Class constructor
	
	Super:C1705()
	
Function clearOutput()
	
	Form:C1466.output:=[]
	
	return Form:C1466
	
Function clearInput()
	
	Form:C1466.input:=""
	
	return Form:C1466
	
Function clearHistory()
	
	Form:C1466.history:=[""]
	
	Form:C1466.selectHistory(0)
	
	return Form:C1466
	
Function rewind()
	
	If (Form:C1466.cursor>0)
		
		Form:C1466.selectHistory(Form:C1466.cursor-1)
		
	End if 
	
	return Form:C1466
	
Function forward()
	
	If (Form:C1466.cursor<(Form:C1466.history.length-1))
		
		Form:C1466.selectHistory(Form:C1466.cursor+1)
		
	End if 
	
	return Form:C1466
	
Function push($line : Text)
	
	Form:C1466.output.push($line)
	
	Form:C1466.clearInput()
	
	OBJECT SET SCROLL POSITION:C906(*; "Output"; Form:C1466.output.length)
	
Function selectHistory($i : Integer)
	
	Form:C1466.cursor:=$i
	LISTBOX SELECT ROW:C912(*; "History"; $i+1)
	Form:C1466.input:=Form:C1466.history[Form:C1466.cursor]
	
Function popupMenu()
	
	If (Contextual click:C713)
		
		$menu:=Create menu:C408
		APPEND MENU ITEM:C411($menu; "クリア"; *)
		SET MENU ITEM PARAMETER:C1004($menu; -1; "clearOutput")
		$command:=Dynamic pop up menu:C1006($menu)
		RELEASE MENU:C978($menu)
		
		If ($command="clearOutput")
			Form:C1466.clearOutput()
		End if 
		
	End if 