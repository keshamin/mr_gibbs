# Create shelve if not exists
import logging
import shelve
import time

import config
from init import bot, app, scheduler
import http_handlers
import tg_handlers


with shelve.open(config.SHELVENAME) as db:
    db['0'] = None

scheduler.start()

tg_handlers.register_handlers(bot)
http_handlers.register_handlers(app)

bot.remove_webhook()

logging.info(f'Starting as {bot.get_me().username}...')
if config.DEBUG:
    bot.polling()
else:
    time.sleep(0.1)
    bot.set_webhook(url=config.WEBHOOK_URL_BASE + config.WEBHOOK_URL_PATH)

    app.run(host=config.WEBHOOK_HOST,
            port=config.WEBHOOK_PORT,
            debug=True)
