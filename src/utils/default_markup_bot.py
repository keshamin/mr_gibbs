from telebot import TeleBot


class DefaultMarkupBot(TeleBot):
    def __init__(self, *args, default_markup, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_markup = default_markup

    def send_message(self, *args, reply_markup=None, **kwargs):
        if reply_markup is None:
            reply_markup = self.default_markup
        return super().send_message(*args, reply_markup=reply_markup, **kwargs)
