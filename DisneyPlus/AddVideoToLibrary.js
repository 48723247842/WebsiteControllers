( async ()=> {
	const RMU = require( "redis-manager-utils" );
	const redis = new RMU( 1 );
	await redis.init();
	let library = JSON.parse( await redis.keyGet( "WEBSITES.LIBRARIES.DISNEY_PLUS" ) );
	library.videos.push({
		"id": "" ,
		"name": "" ,
		"current_time": "0" ,
		"time_remaining": "0"
	});
	await redis.keySet( "WEBSITES.LIBRARIES.DISNEY_PLUS" , JSON.stringify( library ) );
	process.exit( 1 );
})();