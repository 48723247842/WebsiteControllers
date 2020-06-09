import base64

def base64_encode( string ):
	string_bytes = string.encode( "utf-8" )
	base64_bytes = base64.b64encode( string_bytes )
	base64_string = base64_bytes.decode( "utf-8" )
	return base64_string

def base64_decode( string ):
	string_bytes = string.encode( "utf-8" )
	base64_bytes = base64.b64decode( string_bytes )
	message = base64_bytes.decode( "utf-8" )
	return message