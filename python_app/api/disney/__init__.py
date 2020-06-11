import os
import sys
import math
from datetime import datetime
from pathlib import Path
import json
import time
from pprint import pprint
import requests

from sanic import Blueprint
from sanic.response import json as json_result
from sanic import response

import redis
import redis_circular_list
from chrome_rdp_wrapper import ChromeRDPWrapper
from XDoToolWrapper import XDoToolWrapper

from .disney_utils import *

CNEE_DATA_FOLDER_PATH = Path( __file__ ).parents[ 3 ].joinpath( "cnee_files" )
CNEE_CHECK_TIME_PATH = str( CNEE_DATA_FOLDER_PATH.joinpath( "disney_plus_check_time.data" ) )
CNEE_CHECK_PAUSE_AND_TIME_UPDATE = str( CNEE_DATA_FOLDER_PATH.joinpath( "disney_plus_pause_and_time_update.data" ) )
CNEE_PREPARE_NEXT = str( CNEE_DATA_FOLDER_PATH.joinpath( "disney_plus_prepare_next.data" ) )

def playback_next():
	try:
		print( "2.) playback_next()" )

		print( "\tReplay CNEE 'Checking Time'" )
		cnee_check_time()

		redis = redis_connect()
		video = redis_circular_list.next( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
		video = json.loads( video )
		video = update_current_video_time_info( video )

		# 2.) Exit Fullscreen and Manual Time Update
		print( "\tReplay CNEE 'Prepare Next'" )
		cnee_prepare_next()

		# 5.) Open Next Video
		print( "\tOpen Next Video" )
		time.sleep( 3 )
		chrome.open_solo_url( f"https://www.disneyplus.com/video/{video['id']}" )
	except Exception as e:
		PrintException()
		return False

def playback_play():
	try:
		video = update_current_video_time_info()
		if video["over"] == True:
			redis = redis_connect()
			video = redis_circular_list.next( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
			video = json.loads( video )
			video = update_current_video_time_info( video )
		#pprint( video )
		chrome = ChromeRDPWrapper()
		chrome.open_solo_url( f"https://www.disneyplus.com/video/{video['id']}" )
		chrome.attach_xdo_tool( "Disney+ | Video Player" )
	except Exception as e:
		PrintException()
		return False

def playback_stop():
	try:
		# 1.) Manual Get Time Update
		chrome = ChromeRDPWrapper()
		chrome.xdotool = XDoToolWrapper()
		chrome.xdotool.attach_via_name( "Disney+ | Video Player" , 3 , .3 )
		time.sleep( 1 )
		chrome.xdotool.left_click()
		cnee_check_time()
		time.sleep( 2 )

		# 2.) Close all Other Tabs
		chrome.xdotool.press_keyboard_key( "F11" )
		time.sleep( 2 )
		chrome.open_solo_url( "https://www.windy.com/-Thunderstorms-thunder?thunder,39.838,-84.111,5" )
	except Exception as e:
		print( e )
		PrintException()
		return False

def playback_pause():
	try:
		chrome.xdotool.move_mouse( chrome.geometry["center"]["x"] , ( int( chrome.geometry["y"] ) - 30 ) )
		time.sleep( .3 )
		chrome.xdotool.left_click()
		time.sleep( .3 )
		chrome.xdotool.right_click()
		time.sleep( 1 )
		cnee_check_time()
		time.sleep( 1 )
		return True
	except Exception as e:
		print( e )
		return False

def playback_previous():
	try:
		chrome = ChromeRDPWrapper()
		chrome.attach_xdo_tool( "Disney+ | Video Player" )
		tab = chrome_get_disney_tab()
		time.sleep( 1 )
		cnee_check_time()
		chrome.close_tab_id( tab["id"] )
	except Exception as e:
		PrintException()
		return False

def get_chrome_on_disney_player():
	try:
		for i in range( 0 , 10 ):
			try:
				chrome = ChromeRDPWrapper()
				chrome.attach_xdo_tool( "Disney+ | Video Player" )
				# chrome.xdotool = XDoToolWrapper()
				# chrome.xdotool.attach_via_name( "Disney+ | Video Player" , 30 , 1 )
				# chrome.geometry = chrome.xdotool.get_window_geometry()
				tab = chrome_get_disney_tab()
				time.sleep( 1 )
				if chrome.xdotool.window_id is not None and chrome.xdotool.window_id is not False:
					return [ chrome , tab ]
			except Exception as e:
				PrintException()
				return False
	except Exception as e:
		PrintException()
		return False

# def on_agent_reminder():
# 	try:
# 		chrome_stuff = get_chrome_on_disney_player()
# 		chrome = chrome_stuff[0]
# 		tab = chrome_stuff[1]
# 		chrome.xdotool.move_mouse( chrome.geometry["center"]["x"] , chrome.geometry["center"]["y"] )
# 		redis = redis_connect()
# 		video = redis_circular_list.current( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
# 		video = json.loads( video )
# 		if video["playing"]:
# 			chrome.xdotool.press_keyboard_key( "F11" )
# 		else:
# 			chrome.xdotool.press_keyboard_key( "Ctrl+r" )
# 	except Exception as e:
# 		print( e )
# 		return False

def on_agent_ready():
	try:
		# now = datetime.now()
		# now_string = now.strftime( "%d%b%Y = %H:%M:%S.%f" )
		# redis = redis_connect()
		# last_agent_ready_time = redis.get( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.LAST_AGENT_READY_TIME" )
		# if last_agent_ready_time is None:
		# 	last_agent_ready_time = now_string
		# else:
		# 	last_agent_ready_time = str( last_agent_ready_time , 'utf-8' )
		# last_agent_ready_time = datetime.strptime( last_agent_ready_time , "%d%b%Y = %H:%M:%S.%f" )
		# seconds_difference = math.floor( ( now - last_agent_ready_time ).total_seconds() )
		# redis.set( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.LAST_AGENT_READY_TIME" , now_string )
		# time.sleep( 3 )
		# print( "Seconds Difference = " + str( seconds_difference ) )
		# if seconds_difference == 0 or seconds_difference > 25:
		# 	xdotool.press_keyboard_key( "Ctrl+r" )

		# chrome_stuff = get_chrome_on_disney_player()
		# chrome = chrome_stuff[0]
		# tab = chrome_stuff[1]
		# time.sleep( 3 )
		# chrome.xdotool.move_mouse( chrome.geometry["center"]["x"] , chrome.geometry["center"]["y"] )
		#time.sleep( .2 )
		#chrome.xdotool.left_click()
		# requests.post( "http://127.0.0.1:10081/broadcast" , json={
		# 		"message": {
		# 			"channel": "disney_plus" ,
		# 			"message": "agent_acknowledge"
		# 		}
		# 	})
		redis = redis_connect()
		video = redis_circular_list.current( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
		video = json.loads( video )
		pprint( video )
		chrome = ChromeRDPWrapper()
		chrome.attach_xdo_tool( "Disney+ | Video Player" )
		if video["playback_state"] == "playing":
			chrome.xdotool.press_keyboard_key( "F11" )
		else:
			time.sleep( 10 )
			for i in range( 0 , 6 ):
				cnee_check_time()
		print( "done with on_agent_ready()" )
	except Exception as e:
		print( e )
		return False

def on_first_play():
	try:
		for i in range( 0 , 2 ):
			cnee_check_time()
			time.sleep( 2 )
		redis = redis_connect()
		video = redis_circular_list.current( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
		video = json.loads( video )
		pprint( video )
		chrome = ChromeRDPWrapper()
		chrome.attach_xdo_tool( "Disney+ | Video Player" )
		if video["playback_state"] == "playing":
			chrome.xdotool.press_keyboard_key( "F11" )
		else:
			chrome.xdotool.press_keyboard_key( "Ctrl+r" )
	except Exception as e:
		print( e )
		return False

def on_agent_never_connected():
	try:
		pass
		#chrome = ChromeRDPWrapper()
		#chrome.attach_xdo_tool( "Disney+ | Video Player" )
		#chrome.xdotool.press_keyboard_key( "Ctrl+r" )
	except Exception as e:
		print( e )
		return False

disney_blueprint = Blueprint( 'disney' , url_prefix='/disney' )

@disney_blueprint.route( '/' )
def commands_root( request ):
	return response.text( "you are at the websitecontroller:11401/api/disney url\n" )

@disney_blueprint.route( "/ws/consumer" , methods=[ "POST" ] )
async def ws_consumer( request ):
	result = { "message": "failed" }
	try:
		print( "Disney Plus Websocket Consumer" )
		data = request.form
		if "channel" not in data:
			raise Exception( "no channel in message" )
		pprint( data )
		if data["channel"][0] != "disney_plus":
			result["status"] = "channel is not disney"
			raise Exception( "channel is not disney" )
		if "current_time" in data and "time_remaining" in data:
			video = update_current_video_time_info( None , data["current_time"][0] , data["time_remaining"][0] , data["playback_state"][0] )
		else:
			video = update_current_video_time_info()
		result["message"] = "success"
		if video["over"] == True:
			restart_response = requests.get( "http://127.0.0.1:11001/api/button/next" )
			result["status"] = "video is over , pressing Button --> next()"
		if data["message"][0] == "agent_ready":
			print( "Disney Plus Userscript is Ready" )
			on_agent_ready()
		if data["message"][0] == "first_play":
			print( "Disney Plus Userscript says its Playing" )
			on_first_play()
		elif data["message"][0] == "agent_never_connected":
			print( "Disney Plus Userscript Never Connected" )
			on_agent_never_connected()
	except Exception as e:
		PrintException()
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/pause" , methods=[ "GET" ] )
def pause( request ):
	result = { "message": "failed" }
	try:
		playback_pause()
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
async def play( request ):
	result = { "message": "failed" }
	try:
		playback_play()
		result["message"] = "success"
	except Exception as e:
		PrintException()
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
		PrintException()
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
		print( "1.) /next" )
		playback_next()
		result["message"] = "success"
	except Exception as e:
		PrintException()
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/status" , methods=[ "GET" ] )
def status( request ):
	result = { "message": "failed" }
	try:
		redis = redis_connect()
		result["status"] = redis_circular_list.current( redis , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" )
		result["status"] = json.loads( result["status"] )
		result["message"] = "success"
	except Exception as e:
		PrintException()
		result["error"] = str( e )
	return json_result( result )

@disney_blueprint.route( "/time" , methods=[ "GET" ] )
def check_time( request ):
	result = { "message": "failed" }
	try:
		manual_time_check()
		result["message"] = "success"
	except Exception as e:
		PrintException()
		result["error"] = str( e )
	return json_result( result )

