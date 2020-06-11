import os
import sys
import redis
import json
import time

from sanic import Sanic
from sanic.response import json as sanic_json
from sanic.response import file
from sanic import response
from sanic.websocket import ConnectionClosed

from api import api_blueprint

# https://github.com/huge-success/sanic/tree/master/examples
# https://github.com/huge-success/sanic/blob/master/examples/try_everything.py

# https://sanic.readthedocs.io/en/latest/sanic/blueprints.html

app = Sanic( name="Website Controller Server!" )

@app.route( "/" )
def hello( request ):
	return response.text( "You Found the Website Controller Server!\n" )

@app.route( "/ping" )
def ping( request ):
	return response.text( "pong\n" )

@app.route( "/broadcast" , methods=[ "POST" ] )
def broadcast( request ):
	result = { "message": "failed" }
	try:
		message = request.json.get( "json" )
		ws_broadcast( message )
		time.sleep( 1 )
		result["status"] = ""
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

app.blueprint( api_blueprint )

def redis_connect():
	try:
		redis_connection = redis.StrictRedis(
			host="127.0.0.1" ,
			port="6379" ,
			db=1 ,
			#password=ConfigDataBase.self[ 'redis' ][ 'password' ]
			)
		return redis_connection
	except Exception as e:
		return False

def get_config( redis_connection ):
	try:
		try:
			config = redis_connection.get( "CONFIG.WEBSITES_CONTROLLER_SERVER" )
			config = json.loads( config )
			return config
		except Exception as e:
			try:
				config_path = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ) , "config.json" )
				with open( config_path ) as f:
					config = json.load( f )
				redis_connection.set( "CONFIG.WEBSITES_CONTROLLER_SERVER" , json.dumps( config ) )
				return config
			except Exception as e:
				config = {
					"port": 11401 ,
				}
				redis_connection.set( "CONFIG.WEBSITES_CONTROLLER_SERVER" , json.dumps( config ) )
				return config
	except Exception as e:
		print( "Could't Get Config for Website Controller Server" )
		print( e )
		return False

def run_server():
	try:
		redis_connection = redis_connect()
		if redis_connection == False:
			return False
		config = get_config( redis_connection )
		if config == False:
			return False

		host = '0.0.0.0'
		port = config[ 'port' ]
		app.run( host=host , port=port , workers=1 , debug=False )

	except Exception as e:
		print( "Couldn't Start Website Controller Server" )
		print( e )
		return False

def try_run_block( options ):
	for i in range( options[ 'number_of_tries' ] ):
		attempt = options[ 'function_reference' ]()
		if attempt is not False:
			return attempt
		print( f"Couldn't Run '{ options[ 'task_name' ] }', Sleeping for { str( options[ 'sleep_inbetween_seconds' ] ) } Seconds" )
		time.sleep( options[ 'sleep_inbetween_seconds' ] )
	if options[ 'reboot_on_failure' ] == True:
		os.system( "reboot -f" )

try_run_block({
	"task_name": "Website Controller Server" ,
	"number_of_tries": 5 ,
	"sleep_inbetween_seconds": 5 ,
	"function_reference": run_server ,
	"reboot_on_failure": True
	})