import flask
import transmissionrpc

from . import config
from .messages import M
from .mr_gibbs import MrGibbsBot

bot = MrGibbsBot(config.TOKEN)
app = flask.Flask(__name__)
transmission = transmissionrpc.Client(config.TRANS_HOST, config.TRANS_PORT,
                                      user=config.TRANS_USER, password=config.TRANS_PASSWORD)
m = M()
