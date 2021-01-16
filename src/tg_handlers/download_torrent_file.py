import io
import shelve

import requests
from telebot import TeleBot

import config
from utils import extract_filename


def register_handlers(bot: TeleBot):
    @bot.callback_query_handler(lambda cb: cb.data == 'download_torrent')
    def download_torrent(cb):
        with shelve.open(config.SHELVENAME) as db:
            link_key = f'{cb.message.chat.id}_link'
            if link_key not in db:
                bot.send_message(cb.message.chat.id, m.LINK_NOT_FOUND_IN_DB)
                return
            link = db[f'{cb.message.chat.id}_link']
            del db[f'{cb.message.chat.id}_link']

        r = requests.get(link)
        filename = extract_filename(r.headers)
        file_like = io.BytesIO(r.content)
        file_like.name = filename if filename else 'file.torrent'

        bot.send_document(cb.message.chat.id, file_like)

        bot.delete_message(cb.message.chat.id, cb.message.message_id)
