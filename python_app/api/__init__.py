from sanic import Blueprint

from .amazon import amazon_blueprint
from .disney import disney_blueprint
from .hulu import hulu_blueprint
from .netflix import netflix_blueprint
from .twitch import twitch_blueprint
from .youtube import youtube_blueprint

api_blueprint = Blueprint.group(
	amazon_blueprint , disney_blueprint , hulu_blueprint ,
	netflix_blueprint , twitch_blueprint , youtube_blueprint ,
	url_prefix='/api'
	)