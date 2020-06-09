( async ()=> {
	const RMU = require( "redis-manager-utils" );
	const redis = new RMU( 1 );
	await redis.init();
	const readfile = require( "fs" ).readFileSync;
	let lines = readfile( "/home/morphs/WORKSPACE/PROJECTS/MEDIABOX/WebsiteControllers/DisneyPlus/HaleysDisneyPlusLibrary27MAY2020.txt" , "utf-8" );
	lines = lines.split(/\r?\n/);
	let videos = [];
	for ( let i = 0; i < lines.length; ++i ) {
		const items = lines[ i ].split( " - " );
		const name = items[ 0 ];
		const id = items[ 1 ];
		videos.push({
			"id": id ,
			"name": name ,
			"current_time": "0" ,
			"time_remaining": "0"
		});
	}
	const our_disney_plus_library = {
		"videos": videos ,
		"current_video_index": 0
	};
	await redis.keySet( "WEBSITES.LIBRARIES.DISNEY_PLUS" , JSON.stringify( our_disney_plus_library ) );
	process.exit( 1 );
})();