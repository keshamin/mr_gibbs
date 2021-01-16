import shelve

import telebot

import config
import forms


MAX_INPUT_FILE_SIZE = 10 ** 6  # ~1 MB


def register_handlers(bot: telebot.TeleBot):
    
    @bot.message_handler(commands=[str(x) for x in range(1, 101)])
    def add_torrent_by_number(message: telebot.types.Message):
        num = int(message.text[1:])
        db_num = num - 1
        with shelve.open(config.SHELVENAME) as db:
            try:
                link = db[f'{message.chat.id}_search_results'][db_num]['link']
            except IndexError:
                bot.send_message(message.chat.id, 'Торрент с номером {} не найден'.format(num))
        form = forms.AddTorrentForm()
        form.torrent_link = link
        form.fields.location.choices = list(config.CATEGORIES.values())
        form.send_form(message.chat.id)

    @bot.message_handler(content_types=['document'])
    def handle_torrent_file_from_user(msg: telebot.types.Message):
        doc: telebot.types.Document = msg.document
        if doc.file_size > MAX_INPUT_FILE_SIZE:
            bot.reply_to(msg, 'Это слишком большой файл. Это точно .torrent ?')
            return

        link = telebot.apihelper.get_file_url(token=config.TOKEN, file_id=doc.file_id)
        form = forms.AddTorrentForm()
        form.torrent_link = link
        form.fields.location.choices = list(config.CATEGORIES.values())
        form.send_form(msg.chat.id)
