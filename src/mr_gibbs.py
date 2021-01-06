from telebot import TeleBot

from .markups import main_markup


class MrGibbsBot(TeleBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def send_message(self, *args, reply_markup=main_markup, **kwargs):
        return super().send_message(*args, reply_markup=reply_markup, **kwargs)
