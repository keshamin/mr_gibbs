import shelve

import telebot

import config
from utils import get_legal_users_ids


def register_handlers(bot: telebot.TeleBot):
    @bot.message_handler(func=lambda message: message.chat.id not in get_legal_users_ids())
    def permission_denied(message):
        bot.send_message(message.chat.id, 'Доступ запрещен (Permission denied).')

    @bot.message_handler(commands=['start'])
    def start(message):
        with shelve.open(config.SHELVENAME) as db:
            db[f'{message.chat.id}_hash_aliases'] = {}
            db[f'{message.chat.id}_file_message_id'] = None
        bot.send_message(message.chat.id, 'Welcome')
