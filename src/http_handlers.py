import flask
import telebot

from . import tg_handlers, config
from .init import app, bot


@app.route(config.WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


@app.route('/suggest', methods=['POST'])
def handle_suggestion():
    title = flask.request.get_json()['title']
    tg_handlers.rutor_search(config.ADMIN_ID, title)
    return flask.Response(status=200)
