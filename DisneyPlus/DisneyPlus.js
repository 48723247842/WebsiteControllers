#!/usr/bin/env node

const process = require( "process" );
const ChromeWrapper = require( "chromewrapper" );
const RMU = require( "redis-manager-utils" );

// https://stackoverflow.com/a/840808
function get_duplicates( array ) {
	let sorted_arr = array.slice().sort();
	let results = [];
	for ( let i = 0; i < sorted_arr.length - 1; i++) {
		if (sorted_arr[i + 1] == sorted_arr[i]) {
			results.push(sorted_arr[i]);
		}
	}
	return results;
}

class DisneyPlus {

	constructor( options = {} ) {
		this.options = options;
	}

	sleep( milliseconds ) {
		return new Promise( ( resolve ) => { setTimeout( resolve , milliseconds ); } );
	}

	// Addon to redis-manager-utils
	redis_lset( list_key , index , data ) {
		return new Promise( function( resolve , reject ) {
			try {
				this.redis.redis.lset( list_key , index , data , ( err , key ) => {
					resolve();
					return;
				});
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	init() {
		return new Promise( async function( resolve , reject ) {
			try {
				this.chrome_wrapper = new ChromeWrapper( { websocket_server: { port: 10081 } } );
				this.redis = new RMU( 1 );
				await this.redis.init();
				this.status = "stopped";
				this.chrome_wrapper.events.on( "websocket_message_disney_plus" , ( data ) => {
					//console.log( data );
					switch( data[ "message" ] ) {
						case "agent_ready":
							this.page_ready();
							break;
						case "mouse_inside_video_window":
							//this.chrome_wrapper.events.emit( "websocket_broadcast_to_clients" , { "channel": "disney_plus" , "message": "manual_get_time" } );
							break;
						case "time_update":
							this.save_current_time( data[ "current_time" ] , data[ "time_remaining" ] );
							break;
						case "manual_get_time":
							this.manual_get_time();
							break;
						case "manual_time_update":
							this.save_current_time( data[ "current_time" ] , data[ "time_remaining" ] );
							break;
						case "start":
							this.play_next_in_library();
							break;
						case "random":
							this.play_random_in_library();
							break;
						case "next":
							this.play_next_in_library( true );
							break;
						case "previous":
							this.play_previous_in_library();
							break;
						case "pause":
							this.pause();
							break;
						case "resume":
							this.resume();
							break;
						case "pause_resume":
							this.pause_resume();
							break;
						case "stop":
							this.stop();
							break;
						case "status":
							this.chrome_wrapper.events.emit( "websocket_broadcast_to_clients" , {
								"channel": "disney_plus" ,
								"message": "status" ,
								"status": this.status
							});
							break;
						default:
							console.log( data );
					}
				});
				process.on( "unhandledRejection" , async function( reason , p ) {
					console.log( reason );
					console.log( p );
				}.bind( this ) );
				process.on( "uncaughtException" , async function( err ) {
					console.log( err );
				}.bind( this ) );
				process.on( "SIGINT" , async function () {
					process.exit( 1 );
				}.bind( this ) );
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	parse_time_remaining( time_remaining ) {
		if ( !time_remaining ) {
			return {
				hours_remaining: 0 ,
				minutes_remaining: 0 ,
				seconds_remaining: 0 ,
			};
		}
		time_remaining = time_remaining.split( ":" );
		let hours_remaining = 0;
		let minutes_remaining = 0;
		let seconds_remaining = 0;
		switch( time_remaining.length ) {
			case 3:
				hours_remaining = time_remaining[ 0 ];
				minutes_remaining = time_remaining[ 1 ];
				seconds_remaining = time_remaining[ 2 ];
				break;
			case 2:
				minutes_remaining = time_remaining[ 0 ];
				seconds_remaining = time_remaining[ 1 ];
				break;
			case 1:
				seconds_remaining = time_remaining[ 0 ];
				break;
			default:
				console.log( "no time remaining ??" );
		}
		return {
			hours_remaining: hours_remaining ,
			minutes_remaining: minutes_remaining ,
			seconds_remaining: seconds_remaining ,
		};
	}

	is_video_over( time_remaining ) {
		let { hours_remaining , minutes_remaining , seconds_remaining } = this.parse_time_remaining( time_remaining );
		if ( hours_remaining < 1 && minutes_remaining < 3 ) {
			return true;
		}
		return false;
	}

	page_ready() {
		return new Promise( async function( resolve , reject ) {
			try {
				console.log( "Disney+ Userscript Says its Ready for Us" );
				// Somehow xdotool is always wrong with the centers;
				// try again ?
				await this.sleep( 1000 );
				await this.chrome_wrapper.xdotool.windowGeometry();
				this.window_center_x = ( this.chrome_wrapper.xdotool.window_geometry.geometry.x / 2 );
				this.window_center_y = ( this.chrome_wrapper.xdotool.window_geometry.geometry.y / 2 );
				console.log( "\nCentering Mouse" );
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x , this.window_center_y );
				await this.sleep( 3000 );
				await this.infer_stuff_from_current_time_stream();
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	infer_stuff_from_current_time_stream() {
		return new Promise( async function( resolve , reject ) {
			try {
				const time_stream = await this.redis.listGetFull( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.CURRENT_TIME_STREAM" );
				// Pause Detection
				console.log( "\nCurrent Time Stream === " );
				console.log( time_stream );
				const duplicates = get_duplicates( time_stream );
				console.log( "\nDuplicate Items in Current Time Stream ===" );
				console.log( duplicates );
				// await this.redis.keySet( "STATE.WEBSITES.DISNEY_PLUS.PLAYING" , true );
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	save_current_time( current_time="0" , time_remaining="0"  ) {
		return new Promise( async function( resolve , reject ) {
			try {
				console.log( `Current Time === ${current_time}` );
				let current_video_index = parseInt( await this.redis.keyGet( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS.INDEX" ) );
				let current_video = JSON.parse( await this.redis.listGetByIndex( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" , current_video_index ) );
				current_video.current_time = current_time;
				current_video.time_remaining = time_remaining;
				await this.redis_lset( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" , current_video_index , JSON.stringify( current_video ) );
				await this.redis.listRPUSH( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.CURRENT_TIME_STREAM" , current_time );
				const stream_length = parseInt( await this.redis.listGetLength( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.CURRENT_TIME_STREAM" ) );
				if ( stream_length > 30 ) {
					this.redis.listLPOP( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.CURRENT_TIME_STREAM" );
				}
				await this.infer_stuff_from_current_time_stream();
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	watch_video_id( video_id ) {
		return new Promise( async function( resolve , reject ) {
			try {
				await this.chrome_wrapper.killChrome();
				await this.sleep( 1000 );
				await this.chrome_wrapper.openURLInAppMode( `https://www.disneyplus.com/video/${video_id}` , "Disney+ | Video Player" );
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	manual_get_time() {
		return new Promise( async function( resolve , reject ) {
			try {
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x , this.chrome_wrapper.xdotool.window_geometry.geometry.y - 30 );
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x - 130 , this.chrome_wrapper.xdotool.window_geometry.geometry.y - 30 );
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x - 160 , this.chrome_wrapper.xdotool.window_geometry.geometry.y - 30 );
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x - 130 , this.chrome_wrapper.xdotool.window_geometry.geometry.y - 30 );
				this.chrome_wrapper.events.emit( "websocket_broadcast_to_clients" , { "channel": "disney_plus" , "message": "manual_get_time" } );
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	play_next_in_library( override_current_unfinished=false ) {
		return new Promise( async function( resolve , reject ) {
			try {
				let current_video;
				if ( !override_current_unfinished ) {
					let current_video_index = parseInt( await this.redis.keyGet( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS.INDEX" ) );
					if ( !current_video_index ) { current_video_index = 0; }
					current_video = JSON.parse( await this.redis.listGetByIndex( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" , current_video_index ) );
					if ( this.is_video_over( current_video.time_remaining ) ) {
						current_video = await this.redis.nextInCircularList( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" );
						current_video = JSON.parse( current_video[ 0 ] );
					}
				}
				else {
					current_video = await this.redis.nextInCircularList( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" );
					current_video = JSON.parse( current_video[ 0 ] );
				}
				await this.redis.keyDel( "STATE.WEBSITES.DISNEY_PLUS.NOW_PLAYING.CURRENT_TIME_STREAM" );
				console.log( "Up Next === ");
				console.log( current_video );
				await this.watch_video_id( current_video.id );
				this.status = "playing";
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	play_previous_in_library() {
		return new Promise( async function( resolve , reject ) {
			try {
				let previous_video = await this.redis.previousInCircularList( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" );
				previous_video = JSON.parse( previous_video[ 0 ] );
				console.log( "Up Next === ");
				console.log( previous_video );
				await this.watch_video_id( previous_video.id );
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	// play_random_in_library() {
	// 	return new Promise( async function( resolve , reject ) {
	// 		try {
	// 			const next_video = await this.get_next_video();
	// 			await this.watch_video_id( next_video.id );
	// 			resolve();
	// 			return;
	// 		}
	// 		catch( error ) { console.log( error ); resolve( false ); return; }
	// 	}.bind( this ) );
	// }

	pause() {
		return new Promise( async function( resolve , reject ) {
			try {
				const playing = JSON.parse( await this.redis.keyGet( "STATE.WEBSITES.DISNEY_PLUS.PLAYING" ) );
				console.log( `DisneyPlus.js --> pause() --> STATE.WEBSITES.DISNEY_PLUS.PLAYING === ${playing}` );
				if ( playing === false ) { resolve(); return; }
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x , this.window_center_y );
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x + 30 , this.window_center_y + 30 );
				await this.chrome_wrapper.xdotool.rightClick();
				await this.manual_get_time();
				this.status = "paused";
				await  this.redis.keySet( "STATE.WEBSITES.DISNEY_PLUS.STATUS" , this.status )
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	resume() {
		return new Promise( async function( resolve , reject ) {
			try {
				let playing = JSON.parse( await this.redis.keyGet( "STATE.WEBSITES.DISNEY_PLUS.PLAYING" ) );
				if ( playing === true ) { resolve(); return; }
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x , this.window_center_y );
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x + 30 , this.window_center_y + 30 );
				await this.chrome_wrapper.xdotool.rightClick();
				await this.manual_get_time();
				this.status = "playing";
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	pause_resume() {
		return new Promise( async function( resolve , reject ) {
			try {
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x , this.window_center_y );
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x + 30 , this.window_center_y + 30 );
				await this.chrome_wrapper.xdotool.rightClick();
				await this.manual_get_time();
				if ( this.status === "playing" ) { this.status = "paused"; }
				else { this.status = "playing"; }
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}


	stop() {
		return new Promise( async function( resolve , reject ) {
			try {
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x , this.window_center_y );
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x + 30 , this.window_center_y + 30 );
				await this.chrome_wrapper.xdotool.rightClick();
				await this.manual_get_time();
				await this.chrome_wrapper.killChrome();
				this.status = "stopped";
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

}

( async ()=> {
	const disneyplus = new DisneyPlus();
	await disneyplus.init();
})();