import flask

from . import config
from .mr_gibbs import MrGibbsBot

bot = MrGibbsBot(config.TOKEN)
app = flask.Flask(__name__)
