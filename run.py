# Create shelve if not exists
import shelve
import time

from src import config
from src.init import bot, app, scheduler

# Registering HTTP and Telegram handlers
import src.http_handlers
import src.tg_handlers

with shelve.open(config.SHELVENAME) as db:
    db['0'] = None


scheduler.start()

bot.remove_webhook()
if config.DEBUG:
    bot.polling()
else:
    time.sleep(0.1)
    bot.set_webhook(url=config.WEBHOOK_URL_BASE + config.WEBHOOK_URL_PATH)

    app.run(host=config.WEBHOOK_HOST,
            port=config.WEBHOOK_PORT,
            debug=True)
