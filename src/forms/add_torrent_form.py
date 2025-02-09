import base64
import io

import requests
from telebot import types as tb_types

import utils
from formats import render_status_message
from vendor import formgram as fg
from init import bot, transmission


def submit_handler(form: 'AddTorrentForm', callback: tb_types.CallbackQuery):

    response = requests.get(form.torrent_link)

    if not response.ok:
        form.bot.send_message(f'Не удалось скачать торрент-файл по ссылке: {form.torrent_link}')
        return

    torrent = transmission.add_torrent(response.content, download_dir=form.location, paused=not form.start_on_add)
    torrent = transmission.get_torrent(torrent.id)

    text, markup = render_status_message(torrent)
    form.bot.send_message(callback.message.chat.id, text, reply_markup=markup)


def download_torrent_handler(form: 'AddTorrentForm', callback: tb_types.CallbackQuery):
    r = requests.get(form.torrent_link)
    filename = utils.extract_filename(r.headers)
    file_like = io.BytesIO(r.content)
    file_like.name = filename if filename else 'file.torrent'

    form.bot.send_document(callback.message.chat.id, file_like)


class AddTorrentForm(fg.BaseForm):
    bot = bot
    submit_callback = submit_handler
    custom_buttons = [
        fg.CustomButton(
            text='💾 Скачать .torrent',
            callback=download_torrent_handler,
            closes_form=True)
    ]

    torrent_link = fg.StrField(label='Ссылка', required=True, read_only=True)
    location = fg.DynamicChoiceField(label='Расположение', required=True)
    start_on_add = fg.BoolField(label='Старт после добавления', initial_value=True, required=True, noneable=False)
