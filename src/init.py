import flask
import transmissionrpc
from apscheduler.schedulers.background import BackgroundScheduler

import config
from markups import main_markup
from messages import M
from utils.default_markup_bot import DefaultMarkupBot

bot = DefaultMarkupBot(config.TOKEN, default_markup=main_markup)
app = flask.Flask(__name__)
transmission = transmissionrpc.Client(config.TRANS_HOST, config.TRANS_PORT,
                                      user=config.TRANS_USER, password=config.TRANS_PASSWORD)
m = M()
scheduler = BackgroundScheduler()
