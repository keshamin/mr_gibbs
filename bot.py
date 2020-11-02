#! /usr/bin/env python3.6
import io
from base64 import b64encode
from typing import Tuple

import flask
import requests
import shelve
import time
from tempfile import NamedTemporaryFile

import telebot
import telebot.types as tb_types
from transmissionrpc import Torrent

from config import *
import config
from smarthomebot import SmartHomeBot
from trans import TorrentStatuses
from utils import get_search_results, prepare_response_list, paths_to_dict, files_dict_part, get_legal_users_ids, \
    extract_filename
from markups import get_inline_action_markup, inline_arrows_markup, get_inline_category_markup, \
    get_inline_confirm_removing_markup, inline_file_browser_expired_markup, get_inline_files_markup, ExtraActions, \
    extra_actions_markup

MAX_INPUT_FILE_SIZE = 10 ** 6   # ~1 MB


# Create shelve if not exists
with shelve.open(SHELVENAME) as db:
    db['0'] = None

bot = SmartHomeBot(TOKEN)


@bot.message_handler(func=lambda message: message.chat.id not in get_legal_users_ids())
def permission_denied(message):
    bot.send_message(message.chat.id, 'Доступ запрещен (Permission denied).')


@bot.message_handler(commands=['start'])
def start(message):
    with shelve.open(SHELVENAME) as db:
        db[f'{message.chat.id}_hash_aliases'] = {}
        db[f'{message.chat.id}_file_message_id'] = None
    bot.send_message(message.chat.id, 'Welcome')


@bot.message_handler(func=lambda message: message.text == 'Торренты ↕️')
def show_all_torrents(message):
    torrents = bot.trans.get_torrents()
    if torrents:
        for t in torrents:
            text, markup = render_status_message(t)
            bot.send_message(message.chat.id, text, reply_markup=markup)
        return
    bot.send_message(message.chat.id, bot.M.NO_TORRENTS)


def render_status_message(torrent: Torrent) -> Tuple[str, tb_types.InlineKeyboardMarkup]:
    simple_template = '{tid}) {status_emoji} {name} ({percent}%)'
    tid = torrent._fields['id'].value
    status_emoji = bot.status_to_emoji[torrent._fields['status'].value]
    text = simple_template.format(tid=tid, name=torrent._fields['name'].value,
                                  status_emoji=status_emoji, percent=int(torrent.progress))
    markup = get_inline_action_markup(tid)
    return text, markup


@bot.message_handler(func=lambda message: message.text == 'Поиск 🔍')
def rutor_search_from_menu(message):
    bot.send_message(message.chat.id, 'Введите поисковый запрос.')
    bot.register_next_step_handler(message, callback=lambda msg: rutor_search(msg.chat.id, msg.text))


def rutor_search(chat_id, search_request):
    results_list = get_search_results(search_request)
    with shelve.open(SHELVENAME) as db:
        db[f'{chat_id}_search_results'] = results_list
        db[f'{chat_id}_search_cursor'] = 0
    first_five = results_list[:5]
    response = prepare_response_list(first_five, start=0)

    # Resetting start_on_add to default
    bot.start_on_add = True

    if len(response) > 0:
        bot.send_message(chat_id, response, reply_markup=inline_arrows_markup)
    else:
        bot.send_message(chat_id, bot.M.NOT_FOUND_ON_TRACKER(search_request))


@bot.message_handler(commands=[str(x) for x in range(1, 101)])
def add_torrent_by_number(message):
    num = int(message.text[1:])
    db_num = num - 1
    with shelve.open(SHELVENAME) as db:
        try:
            link = db[f'{message.chat.id}_search_results'][db_num]['link']
            db[f'{message.chat.id}_link'] = link
            bot.send_message(message.chat.id, 'Пришли категорию', reply_markup=get_inline_category_markup(message.chat.id))
        except IndexError:
            bot.send_message(message.chat.id, 'Торрент с номером {} не найден'.format(num))


@bot.callback_query_handler(lambda callback: callback.data.split()[0].lower() == 'start_stop')
def start_stop_torrent(callback: tb_types.CallbackQuery):
    tid = callback.data.split()[1]
    try:
        torrent = bot.trans.get_torrent(tid)
    except KeyError:
        bot.send_message(callback.message.chat.id, f'Торрент #{tid} не существует!')
        return

    if torrent.status == TorrentStatuses.STOPPED:
        torrent.start()
    else:
        torrent.stop()

    torrent = bot.trans.get_torrent(tid)
    text, markup = render_status_message(torrent)
    bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(lambda callback: callback.data.split()[0].lower() == 'remove')
def remove_torrent(callback):
    tid = callback.data.split()[1]
    bot.send_message(callback.message.chat.id, bot.M.REMOVE_CONFIRMATION(tid),
                     reply_markup=get_inline_confirm_removing_markup(tid))


@bot.callback_query_handler(lambda cb: cb.data.startswith('confirm_removing'))
def confirm_removing(callback):
    answer, tid, expire_timestamp = callback.data.split()[1:]

    if time.time() > float(expire_timestamp):
        bot.send_message(callback.message.chat.id, bot.M.REMOVE_LINK_EXPIRED)
        return

    if answer == 'torrent_only':
        bot.trans.remove_torrent(tid, delete_data=False)
        bot.send_message(callback.message.chat.id, bot.M.TORRENT_REMOVED(tid))
    elif answer == 'torrent_and_data':
        bot.trans.remove_torrent(tid, delete_data=True)
        bot.send_message(callback.message.chat.id, bot.M.TORRENT_AND_DATA_REMOVED(tid))
    elif answer == 'cancel':
        bot.send_message(callback.message.chat.id, bot.M.NOT_REMOVING)
    else:
        bot.send_message(callback.message.chat.id, bot.M.ERROR_INVALID_ANSWER)
        raise ValueError('Invalid data in remove confirmation.')

    bot.delete_message(callback.message.chat.id, callback.message.message_id)


@bot.callback_query_handler(lambda cb: cb.data == 'extra_actions')
def show_exta_actions(cb: tb_types.CallbackQuery):
    bot.edit_message_reply_markup(cb.message.chat.id, cb.message.message_id, reply_markup=extra_actions_markup)


@bot.callback_query_handler(lambda callback: callback.data.split()[0] in CATEGORIES.keys())
def _get_inline_category_and_add(cb):
    print(cb.data)
    download_dir = CATEGORIES[cb.data.split()[0]]
    with shelve.open(SHELVENAME) as db:
        link_key = f'{cb.message.chat.id}_link'
        if link_key not in db:
            bot.send_message(cb.message.chat.id, bot.M.LINK_NOT_FOUND_IN_DB)
            return
        link = db[f'{cb.message.chat.id}_link']
        del db[f'{cb.message.chat.id}_link']

    response = requests.get(link)
    if not response.ok:
        bot.send_message(f'Не удалось скачать торрент-файл по ссылке: {link}')
        return

    torrent_base64 = b64encode(response.content).decode()
    torrent = bot.trans.add_torrent(torrent_base64, download_dir=download_dir, paused=not bot.start_on_add)
    tid = torrent._fields['id'].value
    bot.send_message(cb.message.chat.id, 'Торрент добавлен под номером {}'.format(tid))


@bot.callback_query_handler(lambda cb: cb.data == 'download_torrent')
def download_torrent(cb):
    with shelve.open(SHELVENAME) as db:
        link_key = f'{cb.message.chat.id}_link'
        if link_key not in db:
            bot.send_message(cb.message.chat.id, bot.M.LINK_NOT_FOUND_IN_DB)
            return
        link = db[f'{cb.message.chat.id}_link']
        del db[f'{cb.message.chat.id}_link']

    r = requests.get(link)
    filename = extract_filename(r.headers)
    file_like = io.BytesIO(r.content)
    file_like.name = filename if filename else 'file.torrent'

    bot.send_document(cb.message.chat.id, file_like)

    bot.delete_message(cb.message.chat.id, cb.message.message_id)


@bot.callback_query_handler(lambda callback: callback.data.lower() in ('left', 'right'))
def turn_page(cb):
    if cb.data.lower() == 'left':
        k = -1
    elif cb.data.lower() == 'right':
        k = 1
    with shelve.open(SHELVENAME) as db:
        cursor = db[f'{cb.message.chat.id}_search_cursor']
        lenght = len(db[f'{cb.message.chat.id}_search_results'])
        control_points = [x for x in range(lenght) if x % 5 == 0]
        start = control_points[(control_points.index(cursor) + k) % len(control_points)]
        if cursor != start:
            results_list = db[f'{cb.message.chat.id}_search_results'][start:start + 5]
            db[f'{cb.message.chat.id}_search_cursor'] = start
            response = prepare_response_list(results_list, start=start)
            bot.edit_message_text(response, chat_id=cb.message.chat.id,
                                  message_id=cb.message.message_id, reply_markup=inline_arrows_markup)
        else:
            bot.answer_callback_query(cb.id, 'У меня больше нет страниц', show_alert=False)


@bot.callback_query_handler(lambda callback: callback.data.lower() == 'dont_start')
def dont_start_on_add(cb):
    bot.start_on_add = False
    bot.send_message(cb.message.chat.id, 'Торрент будет приостановлен после доставления')


@bot.callback_query_handler(lambda cb: cb.data.split()[0].lower() == 'files')
def show_files(callback):
    tid = callback.data.split()[1]

    files = bot.trans.get_files(tid)[int(tid)]
    for file_id in files:
        files[file_id]['file_id'] = file_id

    files_dict = paths_to_dict(files)

    with shelve.open(SHELVENAME) as db:
        db[f'{callback.message.chat.id}_files_tid'] = tid
        db[f'{callback.message.chat.id}_files_dict'] = files_dict
        db[f'{callback.message.chat.id}_hash_aliases'] = {}  # Resetting hashes to keep storage tiny
        last_file_browser_id = db[f'{callback.message.chat.id}_file_message_id']

        if last_file_browser_id:
            bot.edit_message_reply_markup(callback.message.chat.id,
                                          message_id=last_file_browser_id,
                                          reply_markup=inline_file_browser_expired_markup)

    markup = get_inline_files_markup(tid=tid, files_dict=files_dict)
    msg = bot.send_message(callback.message.chat.id, 'Файлы торрента #{}'.format(tid), reply_markup=markup)

    with shelve.open(SHELVENAME) as db:
        db[f'{callback.message.chat.id}_file_message_id'] = msg.message_id


@bot.callback_query_handler(lambda cb: cb.data.split()[0].lower() == 'go_to')
def go_to_files(callback):
    cb_splitted = callback.data.split()
    tid = cb_splitted[1]

    hexhash = cb_splitted[2]
    # go_to = ' '.join(cb_splitted[2:]) if len(cb_splitted) > 2 else None    # None in case when we return to root

    with shelve.open(SHELVENAME) as db:
        files_dict = db[f'{callback.message.chat.id}_files_dict']
        shelved_tid = db[f'{callback.message.chat.id}_files_tid']

        # Unhashing go_to path
        go_to = db[f'{callback.message.chat.id}_hash_aliases'][hexhash]
        if go_to == '':
            go_to = None

    if shelved_tid != tid:
        # Interaction with old file browser
        bot.send_message(callback.message.chat.id, bot.M.FILE_BROWSER_EXPIRED)
        return

    if go_to is not None:
        files_subdict = files_dict_part(files_dict, path=go_to)

        if 'file_id' in files_subdict and isinstance(files_subdict['file_id'], int):
            # Clicking on file
            bot.answer_callback_query(callback.id, bot.M.CLICKING_FILE, show_alert=False)
            return

    markup = get_inline_files_markup(tid=tid, files_dict=files_dict, current_position=go_to)
    bot.edit_message_reply_markup(callback.message.chat.id, message_id=callback.message.message_id,
                                  reply_markup=markup)


@bot.callback_query_handler(lambda cb: cb.data.startswith('check ') or cb.data.startswith('uncheck '))
def check_files(callback):
    action, tid, hexhash = callback.data.split()

    with shelve.open(SHELVENAME) as db:
        path = db[f'{callback.message.chat.id}_hash_aliases'][hexhash]

    feed = {
        tid: {}
    }
    for file_id in bot.file_ids_by_path(tid, path):
        feed[tid][file_id] = {
            'selected': True if action == 'check' else False
        }

    bot.trans.set_files(feed)

    if action == 'check':
        bot.send_message(callback.message.chat.id, bot.M.FILES_MARKED(tid=tid, path=path))
    else:
        bot.send_message(callback.message.chat.id, bot.M.FILES_UNMARKED(tid=tid, path=path))


@bot.callback_query_handler(lambda cb: cb.data == ExtraActions.BACK_TO_MAIN)
def back_to_main_actions(cb: tb_types.CallbackQuery):
    origin_msg: tb_types.Message = cb.message
    tid = origin_msg.text[:origin_msg.text.find(')')]
    main_markup = get_inline_action_markup(tid)
    bot.edit_message_reply_markup(cb.message.chat.id, cb.message.message_id, reply_markup=main_markup)


@bot.message_handler(content_types=['document'])
def handle_torrent_file_from_user(msg: tb_types.Message):
    doc: tb_types.Document = msg.document
    if doc.file_size > MAX_INPUT_FILE_SIZE:
        bot.reply_to(msg, 'Это слишком большой файл. Это точно .torrent ?')
        return

    with shelve.open(SHELVENAME) as database:
        database[f'{msg.chat.id}_link'] = telebot.apihelper.get_file_url(token=TOKEN, file_id=doc.file_id)
        bot.send_message(msg.chat.id, 'Пришли категорию', reply_markup=get_inline_category_markup(msg.chat.id))


@bot.callback_query_handler(lambda: True)
def default_cb(cb):
    print(cb.data)


app = flask.Flask(__name__)


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
    rutor_search(config.ADMIN_ID, title)
    return flask.Response(status=200)


if __name__ == '__main__':
    if config.DEBUG:
        bot.polling()

    else:
        bot.remove_webhook()
        time.sleep(0.1)
        bot.set_webhook(url=config.WEBHOOK_URL_BASE + config.WEBHOOK_URL_PATH)

        app.run(host=config.WEBHOOK_HOST,
                port=config.WEBHOOK_PORT,
                debug=True)
