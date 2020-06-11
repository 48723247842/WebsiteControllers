from chrome_rdp_wrapper import ChromeRDPWrapper
import os
import subprocess
import redis
import json
import math
import redis_circular_list
from datetime import datetime
from datetime import time as datetime_time
import linecache
import sys
from pprint import pprint

def PrintException():
	exc_type, exc_obj, tb = sys.exc_info()
	f = tb.tb_frame
	lineno = tb.tb_lineno
	filename = f.f_code.co_filename
	linecache.checkcache(filename)
	line = linecache.getline(filename, lineno, f.f_globals)
	print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

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
		PrintException()
		return False

# GLOBAL_TIMES = []
def update_current_video_time_info( video=None , current_timestamp=None , remaining_timestamp=None , playback_state="stopped" ):
	global GLOBAL_TIMES
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
		video["playback_state"] = playback_state
		video_index = redis.get( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS.INDEX" )
		video_index = str( video_index , 'utf-8' )
		video["time"]["current"]["minutes"] = current["minutes"]
		video["time"]["current"]["hours"] = current["hours"]
		video["time"]["current"]["seconds"] = current["seconds"]
		video["time"]["current"]["date_string"] = datetime_time( current["hours"] , current["minutes"] , current["seconds"] )
		video["time"]["current"]["date_string"] = video["time"]["current"]["date_string"].strftime( "%H:%M:%S" )
		video["time"]["remaining"]["minutes"] = remaining["minutes"]
		video["time"]["remaining"]["hours"] = remaining["hours"]
		video["time"]["remaining"]["seconds"] = remaining["seconds"]
		video["time"]["remaining"]["date_string"] = datetime_time( remaining["hours"] , remaining["minutes"] , remaining["seconds"] )
		video["time"]["remaining"]["date_string"] = video["time"]["remaining"]["date_string"].strftime( "%H:%M:%S" )
		video["over"] = current["over"]
		pprint( video )
		redis.lset( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" , video_index ,  json.dumps( video ) )
		redis.rpush( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.SNAPSHOTS" ,  json.dumps( video ) )
		length = redis.llen( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.SNAPSHOTS" )
		if length > 100:
			redis.lpop( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.SNAPSHOTS" )
		# GLOBAL_TIMES.append( video["time"]["current"]["date_string"] )
		# print( GLOBAL_TIMES[0] )
		# print( GLOBAL_TIMES[-1] )
		# datetime.strptime( GLOBAL_TIMES[-1] , "%H:%M:%S" )
		# seconds_difference = math.floor( ( datetime.strptime( GLOBAL_TIMES[-1] , "%H:%M:%S" ) - datetime.strptime( GLOBAL_TIMES[0] , "%H:%M:%S" ) ).total_seconds() )
		# print( f"Seconds Difference = {seconds_difference}" )
		# if seconds_difference > 1:
		# 	GLOBAL_TIMES = []
		# 	video["playing"] = True
		# else:
		# 	video["playing"] = False
		return video
	except Exception as e:
		PrintException()
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


def cnee_check_time():
	try:
		cmd_string = "/usr/local/bin/cneeDisneyPlusCheckTime"
		#subprocess.getoutput( cmd_string )
		p = subprocess.Popen(
			cmd_string ,
			cwd=os.getcwd() ,
			stdout=subprocess.PIPE ,
			stderr=subprocess.STDOUT ,
			shell=True
		)
	except Exception as e:
		PrintException()
		return False

def cnee_prepare_next():
	try:
		cmd_string = "/usr/local/bin/cneeDisneyPlusPrepareNext"
		p = subprocess.Popen(
			cmd_string ,
			cwd=os.getcwd() ,
			stdout=subprocess.PIPE ,
			stderr=subprocess.STDOUT ,
			shell=True
		)
	except Exception as e:
		PrintException()
		return False

def replay_cnee_data( file_path , speed_percent=40 ):
	try:
		# Have this just run a bashscript with it?
		# cmd_string = f'DISPLAY=:0.0 cnee --replay --speed-percent {speed_percent} -f "{file_path}" -v -ns &'
		cmd_string = "/usr/local/bin/cneeDisneyPlusCheckTime"
		# subprocess.call( cmd_string , shell=True )
		# subprocess.getoutput( cmd_string )
		p = subprocess.Popen(
			cmd_string ,
			cwd=os.getcwd() ,
			stdout=subprocess.PIPE ,
			stderr=subprocess.STDOUT ,
			shell=True
		)
	except Exception as e:
		PrintException()
		return False

def manual_time_check( chrome=None ):
	try:
		if chrome is None:
			chrome = ChromeRDPWrapper()
		chrome.attach_xdo_tool( "Disney+ | Video Player" )
		chrome.xdotool.move_mouse( chrome.geometry["center"]["x"] , ( int( chrome.geometry["y"] ) - 30 ) )
		cnee_check_time()
		# chrome.xdotool.move_mouse( ( chrome.geometry["center"]["x"] - 130 ) , ( int( chrome.geometry["y"] ) - 20 ) )
		# chrome.xdotool.move_mouse( ( chrome.geometry["center"]["x"] - 160 ) , ( int( chrome.geometry["y"] ) - 20 ) )
		# chrome.xdotool.move_mouse( ( chrome.geometry["center"]["x"] - 190 ) , ( int( chrome.geometry["y"] ) - 20 ) )
		# chrome.xdotool.move_mouse( ( chrome.geometry["center"]["x"] - 120 ) , ( int( chrome.geometry["y"] ) - 20 ) )
		# chrome.xdotool.move_mouse( ( chrome.geometry["center"]["x"] - 150 ) , ( int( chrome.geometry["y"] ) - 20 ) )
	except Exception as e:
		PrintException()
		return False

def locate_disney_tab( page_tabs ):
	for index , tab in enumerate( page_tabs ):
		if "disney" in tab["url"]:
			return tab

def chrome_get_disney_tab():
	try:
		chrome = ChromeRDPWrapper()
		chrome_tabs = chrome.get_tabs()
		page_tabs = [ x for x in chrome_tabs if x["type"] == "page" ]
		return locate_disney_tab( page_tabs )
	except Exception as e:
		PrintException()
		return False

def chrome_close_non_disney_tabs():
	try:
		chrome = ChromeRDPWrapper()
		chrome_tabs = chrome.get_tabs()
		other_tabs = []
		for tab in chrome_tabs:
			if tab is not None:
				if "type" in tab:
					if tab["type"] == "page":
						if "disney" not in tab["url"]:
							chrome.close_tab_id( tab["id"] )
	except Exception as e:
		PrintException()
		return False