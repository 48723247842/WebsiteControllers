const { fork } = require( "child_process" );

function sleep( milliseconds ) {
	return new Promise( ( resolve ) => { setTimeout( resolve , milliseconds ); } );
}

( async ()=> {

	const compute = fork( "DisneyPlus.js" );
	await sleep( 3000 );
	compute.send( "start" );
	compute.on( "message" , ( message ) => {
		console.log( `\ntext_forker.js --> ${message}` );
		switch( message ) {
			case "page_ready":
				setTimeout( () => {
					compute.send( "stop" );
				} , 3200 );
				break;
			default:
				break;
		}
	});

})();