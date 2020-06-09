function sleep( milliseconds ) {
	return new Promise( ( resolve ) => { setTimeout( resolve , milliseconds ); } );
}

function getRandomFromRange( min , max ) { return Math.floor( Math.random() * ( max - min + 1 ) ) + min; }
Math.seed = function( seed ) { return function() { seed = Math.sin( seed ) * 10000; return seed - Math.floor( seed ); }; };
function reseed_math_random() {
	const seed_start = getRandomFromRange( 1 , 100 );
	const random1 = Math.seed( seed_start );
	const random2 = Math.seed( random1() );
	Math.random = Math.seed( random2() );
}

// https://stackoverflow.com/a/6274381
function shuffle( a ) {
	reseed_math_random()
	for ( let i = a.length - 1; i > 0; i-- ) {
		const j = Math.floor( Math.random() * ( i + 1 ) );
		[ a[i] , a[j] ] = [ a[j] , a[i ] ];
	}
	return a;
}

( async ()=> {
	const RMU = require( "redis-manager-utils" );
	const redis = new RMU( 1 );
	await redis.init();
	await redis.keyDel( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" );
	const readfile = require( "fs" ).readFileSync;
	let lines = readfile( "/home/morphs/WORKSPACE/PROJECTS/MEDIABOX/WebsiteControllers/DisneyPlus/HaleysDisneyPlusLibrary27MAY2020.txt" , "utf-8" );
	lines = lines.split(/\r?\n/);
	let multi = [];
	for ( let i = 0; i < lines.length; ++i ) {
		const items = lines[ i ].split( " - " );
		const name = items[ 0 ];
		const id = items[ 1 ];
		const item = JSON.stringify({
			"id": id ,
			"name": name ,
			// "current_time": "0" ,
			// "time_remaining": "0" ,
			"over": false ,
			"time": {
				"current": {
					"stamp": "" ,
					"hours": 0 ,
					"minutes": 0 ,
					"seconds": 0
				} ,
				"remaining": {
					"stamp": "" ,
					"hours": 0 ,
					"minutes": 0 ,
					"seconds": 0
				}
			}
		});
		multi.push( [ "rpush" , "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS" , item ] );
	}
	multi = shuffle( multi );
	multi = shuffle( multi );
	multi = shuffle( multi );
	console.log( multi );
	await redis.keySetMulti( multi );
	await sleep( 3000 );
	await redis.keySet( "STATE.WEBSITES.DISNEY_PLUS.LIBRARY.VIDEOS.INDEX" , 0 );
	process.exit( 1 );
})();