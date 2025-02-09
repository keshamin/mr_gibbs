import flask
import transmission_rpc
from apscheduler.schedulers.background import BackgroundScheduler

import config
from markups import main_markup
from messages import M
from utils.default_markup_bot import DefaultMarkupBot

bot = DefaultMarkupBot(config.TOKEN, default_markup=main_markup)
app = flask.Flask(__name__)
transmission = transmission_rpc.Client(
    protocol=config.TRANS_PROTOCOL,
    host=config.TRANS_HOST,
    port=config.TRANS_PORT,
    username=config.TRANS_USER,
    password=config.TRANS_PASSWORD
)
m = M()
scheduler = BackgroundScheduler()
