from sanic import Blueprint
from sanic.response import json as json_result
from sanic import response

import json
import time
from pprint import pprint

import redis
import redis_circular_list

#from chromewrapper import ChromeWrapper
from chrome_rdp_wrapper import ChromeRDPWrapper
import os
import subprocess
import requests
from pathlib import Path
CNEE_DATA_FOLDER_PATH = Path( __file__ ).parents[ 3 ].joinpath( "cnee_files" )
CNEE_CHECK_TIME_PATH = str( CNEE_DATA_FOLDER_PATH.joinpath( "disney_plus_check_time.data" ) )
CNEE_CHECK_PAUSE_AND_TIME_UPDATE = str( CNEE_DATA_FOLDER_PATH.joinpath( "disney_plus_pause_and_time_update.data" ) )
CNEE_PREPARE_NEXT = str( CNEE_DATA_FOLDER_PATH.joinpath( "disney_plus_prepare_next.data" ) )

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

def update_current_video_time_info( video=None , current_timestamp=None , remaining_timestamp=None ):
	try:
		redis = redis_connect()
		if video == None:
			video = redis_circular_list.current( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
			video = json.loads( video )
		if current_timestamp == None:
			current = parse_timestamp( video["time"]["current"]["stamp"] )
		else:
			current = parse_timestamp( current_timestamp )
			video["time"]["current"]["stamp"] = current_timestamp
		if remaining_timestamp == None:
			remaining = parse_timestamp( video["time"]["current"]["stamp"] )
		else:
			remaining = parse_timestamp( remaining_timestamp )
			video["time"]["remaining"]["stamp"] = remaining_timestamp
		video_index = redis.get( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS.INDEX" )
		video_index = str( video_index , 'utf-8' )
		video["time"]["current"]["minutes"] = current["minutes"]
		video["time"]["current"]["hours"] = current["hours"]
		video["time"]["current"]["seconds"] = current["seconds"]
		video["time"]["remaining"]["minutes"] = remaining["minutes"]
		video["time"]["remaining"]["hours"] = remaining["hours"]
		video["time"]["remaining"]["seconds"] = remaining["seconds"]
		video["over"] = remaining["over"]
		#pprint( video )
		redis.lset( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" , video_index ,  json.dumps( video ) )
		redis.rpush( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.SNAPSHOTS" ,  json.dumps( video ) )
		length = redis.llen( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.SNAPSHOTS" )
		if length > 100:
			redis.lpop( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.SNAPSHOTS" )
		return video
	except Exception as e:
		print( e )
		return False

def play_next_video_in_library( force_next=False ):
	try:
		video = update_current_video_time_info()
		if force_next == True or video["over"] == True:
			redis = redis_connect()
			video = redis_circular_list.next( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
			video = json.loads( video )
			video = update_current_video_time_info( video )
		pprint( video )
		chrome = ChromeRDPWrapper()
		tab = chrome.open_solo_url( f"https://www.disneyplus.com/video/{video['id']}" )
		chrome.enable_runtime_on_tab( tab )
		chrome.attach_xdo_tool( "Disney+ | Video Player" )
		time.sleep( 10 )
		chrome.xdotool.press_keyboard_key( "F11" )
		time.sleep( 1 )
		chrome.xdotool.press_keyboard_key( "Ctrl+r" )
		time.sleep( 3 )
		chrome.xdotool.move_mouse( chrome.geometry["center"]["x"] , chrome.geometry["center"]["y"] )
	except Exception as e:
		print( e )
		return False

def replay_cnee_data( file_path , speed_percent=40 ):
	try:
		cmd_string = f'DISPLAY=:0.0 cnee --replay --speed-percent {speed_percent} -f "{file_path}" -v -e /dev/null -ns'
		subprocess.call( cmd_string , shell=True )
		# p = subprocess.Popen(
		# 	cmd_string ,
		# 	cwd=os.getcwd() ,
		# 	stdout=subprocess.PIPE ,
		# 	stderr=subprocess.STDOUT ,
		# 	shell=True
		# )

	except Exception as e:
		print( e )
		return False

def manual_time_check( chrome=None ):
	try:
		if chrome is None:
			chrome = ChromeRDPWrapper()
		chrome.attach_xdo_tool( "Disney+ | Video Player" )
		chrome.xdotool.move_mouse( chrome.geometry["center"]["x"] , ( int( chrome.geometry["y"] ) - 30 ) )
		print( CNEE_CHECK_TIME_PATH )
		replay_cnee_data( CNEE_CHECK_TIME_PATH )
		# chrome.xdotool.move_mouse( ( chrome.geometry["center"]["x"] - 130 ) , ( int( chrome.geometry["y"] ) - 20 ) )
		# chrome.xdotool.move_mouse( ( chrome.geometry["center"]["x"] - 160 ) , ( int( chrome.geometry["y"] ) - 20 ) )
		# chrome.xdotool.move_mouse( ( chrome.geometry["center"]["x"] - 190 ) , ( int( chrome.geometry["y"] ) - 20 ) )
		# chrome.xdotool.move_mouse( ( chrome.geometry["center"]["x"] - 120 ) , ( int( chrome.geometry["y"] ) - 20 ) )
		# chrome.xdotool.move_mouse( ( chrome.geometry["center"]["x"] - 150 ) , ( int( chrome.geometry["y"] ) - 20 ) )
	except Exception as e:
		print( e )
		return False

def _locate_disney_tab( page_tabs ):
	for index , tab in enumerate( page_tabs ):
		if "disney" in tab["url"]:
			return tab

def chrome_get_disney_tab():
	try:
		chrome = ChromeRDPWrapper()
		chrome_tabs = chrome.get_tabs()
		page_tabs = [ x for x in chrome_tabs if x["type"] == "page" ]
		return _locate_disney_tab( page_tabs_ )
	except Exception as e:
		print( e )
		return False

def chrome_custom_close():
	try:
		replay_cnee_data( CNEE_PREPARE_NEXT )
		chrome = ChromeRDPWrapper()
		tab = chrome.open_solo_url( "https://ceberous.org" )
	except Exception as e:
		print( e )
		return False

def playback_stop():
	try:
		# 1.) Close all Other Tabs
		chrome = ChromeRDPWrapper()
		chrome_tabs = chrome.get_tabs()
		page_tabs = [ x for x in chrome_tabs if x["type"] == "page" ]
		our_tab =_locate_disney_tab( page_tabs )
		other_tabs = [ x for x in page_tabs if x["id"] != our_tab["id"] ]
		for index , tab in enumerate( other_tabs ):
			chrome.close_tab_id( tab["id"] )

		# 2.) Move Mouse to Get Time Updates
		#manual_time_check( chrome )

		# 3.) Close the Tab
		#time.sleep( 1 )
		#chrome.close_tab_id( our_tab["id"] )
		chrome_custom_close()
	except Exception as e:
		print( e )
		return False

def playback_pause():
	try:
		# 1.) Close all Other Tabs
		chrome = ChromeRDPWrapper()
		chrome.attach_xdo_tool( "Disney+ | Video Player" )
		chrome_tabs = chrome.get_tabs()
		page_tabs = [ x for x in chrome_tabs if x["type"] == "page" ]
		our_tab =_locate_disney_tab( page_tabs )
		other_tabs = [ x for x in page_tabs if x["id"] != our_tab["id"] ]
		for index , tab in enumerate( other_tabs ):
			chrome.close_tab_id( tab["id"] )

		# 2.) Move Mouse to Get Time Updates
		chrome.xdotool.move_mouse( chrome.geometry["center"]["x"] , ( int( chrome.geometry["y"] ) - 30 ) )
		time.sleep( 1 )
		replay_cnee_data( CNEE_CHECK_PAUSE_AND_TIME_UPDATE )
		return True
	except Exception as e:
		print( e )
		return False

def playback_previous():
	try:
		chrome = ChromeRDPWrapper()
		chrome.attach_xdo_tool( "Disney+ | Video Player" )
		tab = chrome_get_disney_tab()
		manual_time_check( chrome )
		time.sleep( 1 )
		chrome.close_tab_id( tab["id"] )
	except Exception as e:
		print( e )
		return False

disney_blueprint = Blueprint( 'disney' , url_prefix='/disney' )

@disney_blueprint.route( '/' )
def commands_root( request ):
	return response.text( "you are at the websitecontroller:11401/api/disney url\n" )

@disney_blueprint.route( "/ws/consumer" , methods=[ "POST" ] )
def ws_consumer( request ):
	result = { "message": "failed" }
	try:
		print( "Disney Plus Websocket Consumer" )
		data = request.form
		pprint( data )
		if "channel" not in data:
			raise Exception( "no channel in message" )
		if data["channel"][0] != "disney_plus":
			result["status"] = "channel is not disney"
			raise Exception( "channel is not disney" )
		if "current_time" in data and "time_remaining" in data:
			video = update_current_video_time_info( None , data["current_time"][0] , data["time_remaining"][0] )
		else:
			video = update_current_video_time_info()
		result["message"] = "success"
		if video["over"] == True:
			restart_response = requests.get( "http://127.0.0.1:11001/api/button/next" )
			resonse["status"] = "video is over , pressing Button --> next()"
		if data["message"][0] == "agent_ready":
			print( "Disney Plus Userscript is Ready" )
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/pause" , methods=[ "GET" ] )
def pause( request ):
	result = { "message": "failed" }
	try:
		playback_pause()
		print( "hello ?" )
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/resume" , methods=[ "GET" ] )
def resume( request ):
	result = { "message": "failed" }
	try:
		playback_pause()
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/play" , methods=[ "GET" ] )
def play( request ):
	result = { "message": "failed" }
	try:
		play_next_video_in_library()
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/stop" , methods=[ "GET" ] )
def stop( request ):
	result = { "message": "failed" }
	try:
		playback_stop()
		time.sleep( 1 )
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/previous" , methods=[ "GET" ] )
def previous( request ):
	result = { "message": "failed" }
	try:
		playback_previous()
		time.sleep( 1 )
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/next" , methods=[ "GET" ] )
def next( request ):
	result = { "message": "failed" }
	try:
		replay_cnee_data( CNEE_PREPARE_NEXT )
		play_next_video_in_library( True )
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/status" , methods=[ "GET" ] )
def status( request ):
	result = { "message": "failed" }
	try:
		redis = redis_connect()
		# video_index = redis.get( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS.INDEX" )
		# video_index = str( video_index , 'utf-8' )
		# video = redis.lindex( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" , video_index )
		result["status"] = redis_circular_list.current( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
		result["status"] = json.loads( result["status"] )
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/time" , methods=[ "GET" ] )
def check_time( request ):
	result = { "message": "failed" }
	try:
		manual_time_check()
		result["message"] = "success"
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

