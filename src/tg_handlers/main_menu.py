from telebot import TeleBot

from init import transmission, m
from formats import render_status_message
from tg_handlers.torrent_search import rutor_search


def register_handlers(bot: TeleBot):

    @bot.message_handler(func=lambda message: message.text == 'Торренты ↕️')
    def show_all_torrents(message):
        torrents = transmission.get_torrents()
        if torrents:
            for t in torrents:
                text, markup = render_status_message(t)
                bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        bot.send_message(message.chat.id, m.NO_TORRENTS)

    @bot.message_handler(func=lambda message: message.text == 'Поиск 🔍')
    def rutor_search_from_menu(message):
        bot.send_message(message.chat.id, 'Введите поисковый запрос.')
        bot.register_next_step_handler(message, callback=lambda msg: rutor_search(bot, msg.chat.id, msg.text))
