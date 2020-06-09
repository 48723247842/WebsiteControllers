#!/usr/bin/env node

const process = require( "process" );
const ChromeWrapper = require( "chromewrapper" );
const RMU = require( "redis-manager-utils" );

class DisneyPlus {

	constructor( options = {} ) {
		this.options = options;
		this.paused = true;
		this.playing = false;
	}

	sleep( milliseconds ) {
		return new Promise( ( resolve ) => { setTimeout( resolve , milliseconds ); } );
	}

	init() {
		return new Promise( async function( resolve , reject ) {
			try {
				this.chrome_wrapper = new ChromeWrapper();
				this.redis = new RMU( 1 );
				await this.redis.init();
				this.library = JSON.parse( await this.redis.keyGet( "WEBSITES.LIBRARIES.DISNEY_PLUS" ) );
				this.chrome_wrapper.events.on( "websocket_message_disney_plus" , ( data ) => {
					//console.log( data );
					switch( data[ "message" ] ) {
						case "agent_ready":
							this.page_ready();
							break;
						case "mouse_inside_video_window":
							this.chrome_wrapper.events.emit( "websocket_broadcast_to_clients" , { "channel": "disney_plus" , "message": "manual_get_time" } );
							break;
						case "time_update":
							this.save_current_time( data[ "current_time" ] , data[ "time_remaining" ] );
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
							this.play_next_in_library();
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
						default:
							console.log( data );
					}
				});
				process.on( "unhandledRejection" , async function( reason , p ) {
					console.log( reason );
					console.log( p );
					await this.save_library_to_redis();
				}.bind( this ) );
				process.on( "uncaughtException" , async function( err ) {
					console.log( err );
					await this.save_library_to_redis();
				}.bind( this ) );
				process.on( "SIGINT" , async function () {
					await this.save_library_to_redis();
					process.exit( 1 );
				}.bind( this ) );
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	save_library_to_redis() {
		return new Promise( async function( resolve , reject ) {
			try {
				await this.redis.keySet( "WEBSITES.LIBRARIES.DISNEY_PLUS" , JSON.stringify( this.library ) );
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	parse_time_remaining( time_remaining ) {
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

	get_previous_video() {
		return new Promise( async function( resolve , reject ) {
			try {
				let index = this.library.current_video_index;
				let video = this.library.videos[ index ];
				index -= 1;
				if ( index < 0 ) {
					index = ( this.library.videos.length - 1 );
					console.log( "Recycling to Last Video in Library" );
				}
				this.now_playing = this.library.videos[ index ];
				this.library.current_video_index = index;
				resolve( this.now_playing );
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	get_next_video() {
		return new Promise( async function( resolve , reject ) {
			try {
				let index = this.library.current_video_index;
				let video = this.library.videos[ index ];
				if ( this.is_video_over( video.time_remaining ) ) {
					index += 1;
					console.log( "Last Movie Watched is Presumed to Be Over" );
					console.log( "Advancing to the Next in the List" );
				}
				if ( index >= this.library.videos.length ) {
					index = 0;
					console.log( "Recycling Back to Beginning of Library" );
				}
				this.now_playing = this.library.videos[ index ];
				this.library.current_video_index = index;
				resolve( this.now_playing );
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
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
				this.paused = false;
				this.playing = true;
				process.send( "page_ready" );
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	save_current_time( current_time="0" , time_remaining="0"  ) {
		return new Promise( async function( resolve , reject ) {
			try {
				this.now_playing.current_time = current_time;
				this.now_playing.time_remaining = time_remaining;
				console.log( `Current Time === ${current_time}` );
				await this.save_library_to_redis();
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	watch_video_id( video_id ) {
		return new Promise( async function( resolve , reject ) {
			try {
				await this.chrome_wrapper.openURLInAppMode( `https://www.disneyplus.com/video/${video_id}` , "Disney+ | Video Player" );
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	play_next_in_library() {
		return new Promise( async function( resolve , reject ) {
			try {
				const next_video = await this.get_next_video();
				console.log( "Up Next === ");
				console.log( next_video );
				await this.watch_video_id( next_video.id );
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	play_previous_in_library() {
		return new Promise( async function( resolve , reject ) {
			try {
				const previous_video = await this.get_previous_video();
				console.log( "Up Next === ");
				console.log( next_video );
				await this.watch_video_id( next_video.id );
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
				if ( this.paused === true ) { resolve(); return; }
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x , this.window_center_y );
				await this.sleep( 1000 );
				await this.chrome_wrapper.xdotool.pressKeyboardKey( "Space" );
				this.paused = true;
				this.playing = false;
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

	resume() {
		return new Promise( async function( resolve , reject ) {
			try {
				if ( this.paused === false ) { resolve(); return; }
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x , this.window_center_y );
				await this.sleep( 1000 );
				await this.chrome_wrapper.xdotool.pressKeyboardKey( "Space" );
				this.paused = true;
				this.playing = true;
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
				await this.sleep( 1000 );
				await this.chrome_wrapper.xdotool.pressKeyboardKey( "Space" );
				this.paused = !this.paused;
				this.playing = !this.playing;
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
				await this.chrome_wrapper.xdotool.moveMouse( this.window_center_x + 3 , this.window_center_y + 3 );
				await this.sleep( 1000 );
				await this.chrome_wrapper.killChrome();
				this.paused = true;
				resolve();
				return;
			}
			catch( error ) { console.log( error ); resolve( false ); return; }
		}.bind( this ) );
	}

}

let disneyplus;

( async ()=> {
	disneyplus = new DisneyPlus();
	await disneyplus.init();
	process.on( "message" , ( message ) => {
		console.log( `\nDisneyPlus.js --> process.on(message) --> ${message}` );
		switch( message ) {
			case "start":
				disneyplus.play_next_in_library();
				break;
			case "random":
				disneyplus.play_random_in_library();
				break;
			case "next":
				disneyplus.play_next_in_library();
				break;
			case "previous":
				disneyplus.play_previous_in_library();
				break;
			case "pause":
				disneyplus.pause();
				break;
			case "resume":
				disneyplus.resume();
				break;
			case "pause_resume":
				disneyplus.pause_resume();
				break;
			case "stop":
				disneyplus.stop();
				break;
			default:
				break;
		}
	});
})();