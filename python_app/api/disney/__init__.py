from sanic import Blueprint
from sanic.response import json as json_result
from sanic import response

import json
import time
from pprint import pprint

import redis
import redis_circular_list

#from chromewrapper import ChromeWrapper
import requests

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

def chrome_get_tabs():
	try:
		tabs = requests.get( "127.0.0.1:9222/json" )
		tabs.raise_for_status()
		tabs = tabs.json()
		return tabs
	except Exception as e:
		print( e )
		return False

def chrome_open_tab( url ):
	try:
		result = requests.get( f"http://localhost:9222/json/new?{url}" )
		result.raise_for_status()
		result = result.json()
		return result
	except Exception as e:
		print( e )
		return False

def parse_timestamp( timestamp ):
	result = {
		"over": False ,
		"hours": 0 ,
		"minutes": 0 ,
		"seconds": 0
	}
	items = timestamp.split( ":" )
	length = len( items )
	if items[0] == '':
		return result
	if length == 3:
		result["hours"] = int( items[0] )
		result["minutes"] = int( items[1] )
		result["seconds"] = int( items[2] )
		if result["hours"] <= 0:
			if result["minutes"] <= 0:
				if result["seconds"] <= 30:
					result["over"] = True
	elif length == 2:
		result["minutes"] = int( items[0] )
		result["seconds"] = int( items[1] )
		if result["minutes"] <= 0:
			if result["seconds"] <= 30:
				result["over"] = True
	elif length == 1:
		result["seconds"] = int( items[0] )
		if result["seconds"] <= 30:
			result["over"] = True
	return result

def update_video_time_info( video ):
	current = parse_timestamp( video["time"]["current"]["stamp"] )
	video["time"]["current"]["minutes"] = current["minutes"]
	video["time"]["current"]["hours"] = current["hours"]
	video["time"]["current"]["seconds"] = current["seconds"]
	remaining = parse_timestamp( video["time"]["remaining"]["stamp"] )
	video["time"]["remaining"]["minutes"] = remaining["minutes"]
	video["time"]["remaining"]["hours"] = remaining["hours"]
	video["time"]["remaining"]["seconds"] = remaining["seconds"]
	video["over"] = remaining["over"]
	return video

disney_blueprint = Blueprint( 'disney' , url_prefix='/disney' )

@disney_blueprint.route( '/' )
def commands_root( request ):
	return response.text( "you are at the websitecontroller:11401/api/disney url\n" )

@disney_blueprint.route( "/ws/consumer" , methods=[ "POST" ] )
def ws_consumer( request ):
	result = { "message": "failed" }
	try:
		print( "wadu?" )
		pprint( request.body )
		print( "Disney Plus Websocket Consumer" )
		time.sleep( 1 )
		result["status"] = ""
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/pause" , methods=[ "GET" ] )
def pause( request ):
	result = { "message": "failed" }
	try:
		time.sleep( 1 )
		result["status"] = ""
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/resume" , methods=[ "GET" ] )
def resume( request ):
	result = { "message": "failed" }
	try:
		time.sleep( 1 )
		result["status"] = ""
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/play" , methods=[ "GET" ] )
def play( request ):
	result = { "message": "failed" }
	try:
		redis = redis_connect()
		video = redis_circular_list.current( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
		video = json.loads( video )
		video = update_video_time_info( video )
		if video["over"] == True:
			video = redis_circular_list.next( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
			video = json.loads( video )
			video = update_video_time_info( video )
		pprint( video )




		# chrome = ChromeWrapper({
		# 		"window_name": "Disney+ | Video Player" ,
		# 		"extension_paths": [
		# 			# Tampermonkey
		# 			"/home/morphs/.config/google-chrome/Default/Extensions/dhdgffkkebhmkfjojejmpbldmpobfkfo"
		# 		]
		# 	})
		# chrome.open_in_kiosk_mode( f"https://www.disneyplus.com/video/{video['id']}" )
		# better to wait for {"channel":"disney_plus","message":"agent_ready"}
		# Then send a refresh if its the "first one" aka hasn't sent a refresh in last 30 seconds
		# But for now , just wait 20 seconds , then refresh. bcoz mickey
		#time.sleep( 20 )
		#chrome.xdotool.press_keyboard_key( "Ctrl+r" )

		print( chrome.xdotool.get_window_geometry() )
		time.sleep( 3 )
		chrome.xdotool.fullscreen()
		time.sleep( 1 )
		result["status"] = "unknown"
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/stop" , methods=[ "GET" ] )
def stop( request ):
	result = { "message": "failed" }
	try:
		time.sleep( 1 )
		result["status"] = ""
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/previous" , methods=[ "GET" ] )
def previous( request ):
	result = { "message": "failed" }
	try:
		time.sleep( 1 )
		result["status"] = ""
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/next" , methods=[ "GET" ] )
def next( request ):
	result = { "message": "failed" }
	try:
		time.sleep( 1 )
		result["status"] = ""
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/status" , methods=[ "GET" ] )
def status( request ):
	result = { "message": "failed" }
	try:
		result["status"] = ""
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )