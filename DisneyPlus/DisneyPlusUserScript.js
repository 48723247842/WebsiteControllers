// ==UserScript==
// @name          Disney+ Automator Agent
// @namespace     http://userstyles.org
// @description   Interacts with ChromeWrapper to Automate Disney+
// @author        707433
// @include       *://*disneyplus.com/video/*
// @run-at        document-start
// @version       0.1
// ==/UserScript==

// So just make sure that you install this noramlly in tampermonkey
// or you can do the fancy way of allowing tampermonkey access to file urls
// and then creating a custom userscript that points to this file path
// just remove the hashtags

// ##==UserScript==
// ##@name          Disney+ Automator Agent
// ##@namespace     http://userstyles.org
// ##@description   Interacts with ChromeWrapper to Automate Disney+
// ##@author        707433
// ##@include       *://*disneyplus.com/video/*
// ##@run-at        document-start
// ##@version       0.1
// ##@require       file:///home/morphs/WORKSPACE/PROJECTS/MEDIABOX/WebsiteControllers/DisneyPlus/DisneyPlusUserScript.js
// ##==/UserScript==

var observer_config = {
	childList: true ,
	attributes: true ,
	characterData: true ,
	subtree: true ,
	attributeOldValue: true ,
	characterDataOldValue: true
};
var time_string_oberver = false;
var last_update_time = "00:00:00";
var current_time = "00:00:00";
var time_remaining = "00:00:00";
var websocket_client = false;

// var svg_buttton_click_on_active = false;

function try_websocket_send( javascript_object ) {
	try { websocket_client.send( JSON.stringify( javascript_object ) ); }
	catch( e ) {
		console.log( e );
		//start_websocket_client();
		setTimeout( function() {
			try_websocket_send( javascript_object );
		} , 1500 );
	}
}

function start_websocket_client() {
	//websocket_client = new WebSocket( "ws://127.0.0.1:10081" );
	websocket_client = new WebSocket( "ws://127.0.0.1:10081/ws" );
	websocket_client.onmessage = function ( message ) {
		try { var recieved = JSON.parse( message.data ); }
		catch( e ) { console.log( e ); console.log( message.data ); return; }
		if ( !recieved ) { return; }
		if ( !recieved[ "channel" ] ) { return; }
		if ( recieved[ "channel" ] !== "disney_plus" ) { return; }
		console.log( "Recieved Message from Server" );
		console.log( recieved );
		if ( recieved.message === "manual_get_time" ) {
			try_websocket_send({
				channel: "disney_plus" ,
				message: "manual_time_update" ,
				current_time: current_time ,
				time_remaining: time_remaining
			});
		}
		// else if ( recieved.message === "pause" ) {
		// 	console.log( "DisneyPlusUserScript.js --> pause()" );
		// 	svg_buttton_click_on_active = "pause";
		// }
	}
	websocket_client.onclose = function() {
		ws = false;
		setTimeout( start_websocket_client , 1000 );
	}
}

function get_svg_buttons() {
	var svg_buttons = {};
	var button_elements = document.querySelectorAll( "svg" );
	for ( var i = 0; i < button_elements.length; ++i ) {
		var text = button_elements[ i ][ "innerHTML" ];
		//var text = button_elements[ i ][ "href" ][ "baseVal" ];
		if ( text.indexOf( "left" ) > -1 ) {
			svg_buttons[ "left" ] = button_elements[ i ].parentNode;
		}
		else if ( text.indexOf( "right" ) > -1 ) {
			svg_buttons[ "right" ] = button_elements[ i ].parentNode;
		}
		else if ( text.indexOf( "captioning" ) > -1 ) {
			svg_buttons[ "close_captioning" ] = button_elements[ i ].parentNode;
		}
		else if ( text.indexOf( "play" ) > -1 ) {
			svg_buttons[ "play" ] = button_elements[ i ].parentNode;
		}
		else if ( text.indexOf( "pause" ) > -1 ) {
			svg_buttons[ "pause" ] = button_elements[ i ].parentNode;
		}
		else if ( text.indexOf( "rwd" ) > -1 ) {
			svg_buttons[ "rewind" ] = button_elements[ i ].parentNode;
		}
		else if ( text.indexOf( "ff" ) > -1 ) {
			svg_buttons[ "forward" ] = button_elements[ i ].parentNode;
		}
		else if ( text.indexOf( "fullscreen" ) > -1 ) {
			svg_buttons[ "fullscreen" ] = button_elements[ i ].parentNode;
		}
	}
	return svg_buttons;
}

function on_mouse_over() {
	console.log( "on_mouse_over()" );
	var svg_buttons = get_svg_buttons();
	console.log( svg_buttons );
	var time_string_element = document.querySelector( ".time-display-label" );
	var time_string = time_string_element.innerText.split( " / " );
	current_time = time_string[ 0 ];
	time_remaining = time_string[ 1 ];
	if ( current_time !== last_update_time ) {
		last_update_time = current_time;
	}
	console.log( "Current Time == " + current_time );
	console.log( "Total Time == " + time_remaining );
	try_websocket_send({
		channel: "disney_plus" ,
		message: "time_update" ,
		current_time: current_time ,
		time_remaining: time_remaining
	});
	time_string_oberver = new MutationObserver( function( mutations ) {
		for ( let i = 0; i < mutations.length; ++i ) {
			if ( mutations[ i ][ "target" ][ "parentNode" ][ "className" ] === "time-display-label" ) {
				var time_string = mutations[ i ][ "target" ][ "data" ].split( " / " );
				current_time = time_string[ 0 ];
				time_remaining = time_string[ 1 ];
				if ( current_time === last_update_time ) {
					continue;
				}
				last_update_time = current_time;
				console.log( "Observer --> Current Time == " + current_time );
				console.log( "Observer --> Total Time == " + time_remaining );
				try_websocket_send({
					channel: "disney_plus" ,
					message: "time_update" ,
					current_time: current_time ,
					time_remaining: time_remaining
				});
			}
		}
	});
	time_string_oberver.observe( time_string_element , observer_config );

	// Set Volume Slider to Max
	var volume_slider = document.querySelector( ".slider-container" );
	var current_volume = volume_slider.getAttribute( "aria-valuenow" );
	console.log( "Current Volume === " + current_volume );
	if ( parseInt( current_volume ) < 100 ) {
		console.log( "Volume Not at 100 %" );
		//console.log( "We have to Hover Cursor Directly over Volume Button" );
		// Or you could just "tab-in"
		// aka Click center of screen , the press tab key 6 times
		console.log( "Need to Click Center of Screen , the press tab key 6 times" );
		console.log( "And Then Press 'Up Arrow' Keyboard Key 10 Times" );
		volume_slider.click();
	}

	// Unmute If Muted
	var mute_button = document.querySelector( 'button[aria-label="Volume"' );
	var mute_button_active_classes = mute_button.className;
	if ( mute_button_active_classes.indexOf( "mute-btn--on" ) > -1 ) {
		console.log( "Un-Mutting Volume" );
		mute_button.click();
	}

	// We Need To Somehow Detect if State == Paused or Playing
	// 1.) Move Mouse to Center of Screen , if Time Updates Don't Happen , its paused ?
	// 2.) svg_buttons[ "play" ].click();
	// if ( svg_buttton_click_on_active !== false ) {
	// 	try {
	// 		console.log( "Trying to Click the " + svg_buttton_click_on_active + " button" );
	// 		console.log( svg_buttons[ svg_buttton_click_on_active ] );
	// 		svg_buttons[ svg_buttton_click_on_active ].click();
	// 		svg_buttton_click_on_active = false;
	// 	}
	// 	catch( error ) { console.log( error ); }
	// }
	try_websocket_send({
		channel: "disney_plus" ,
		message: "mouse_inside_video_window" ,
	});
}

function hook_control_buttons() {
	console.log( "Hooking Control Buttons" );
	var video_window = document.querySelector( ".btm-media-overlays-container" );
	video_window.addEventListener( "mouseover" , function() {
		console.log( "We Hovered the Mouse in the right Spot to Enable Media Controls" );
		setTimeout( function() {
			on_mouse_over();
		} , 500 );
	});
	try_websocket_send({
		channel: "disney_plus" ,
		message: "agent_ready" ,
	});
}

function init() {
	start_websocket_client();
	console.log( "We Found .btm-media-overlays-container " );
	setTimeout( function() {
		hook_control_buttons();
	} , 3000 );
}

(function() {
	var READY_CHECK_INTERVAL = setInterval(function(){
		var x1 = document.querySelectorAll( '.btm-media-overlays-container' );
		if ( x1 ) { if ( x1[ 0 ] ) { clearInterval( READY_CHECK_INTERVAL ); init(); } }
	} , 2 );
	setTimeout( function() {
		clearInterval( READY_CHECK_INTERVAL );
	} , 10000 );
})();