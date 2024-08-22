If (FORM Event:C1606.code=On Clicked:K2:4)
	
	Form:C1466.input:="date_default_timezone_set('Asia/Tokyo');foreach (date_sun_info(time(), 35.68949, 139.69171) as $key => $val) {echo \"$key: \" . date(\"H:i:s\", $val) . \"\\n\";};"
	
End if 