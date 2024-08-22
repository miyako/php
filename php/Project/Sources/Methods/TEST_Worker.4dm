//%attributes = {}
If (Is Windows:C1573)
	$ini:=File:C1566("/RESOURCES/php/php.ini")
End if 

$CGI:=cs:C1710.PHP_CGI.new(cs:C1710._PHP_CGI_Controller; $ini).cgi()

$CGI.terminate()

$f:=File:C1566("/RESOURCES/php/function.php")
$f:=OB Class:C1730($f).new($f.platformPath; fk platform path:K87:2)

var $returnValue : Text

If (PHP Execute:C1058($f.platformPath; "sum"; $returnValue; 5; 3))
	
	ALERT:C41($returnValue)
	
End if 