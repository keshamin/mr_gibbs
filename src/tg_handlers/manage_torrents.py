import shelve
import time
from typing import Union

import telebot
import transmissionrpc

import config
from formats import parse_tid_from_status_message, render_status_message
from init import transmission, m, scheduler
from markups import get_inline_confirm_removing_markup, CallbackCommands, extra_actions_markup, \
    inline_file_browser_expired_markup, get_inline_files_markup, ExtraActions, get_inline_action_markup, cancel_markup
from transmission_utils import TorrentStatus
from utils import paths_to_dict, files_dict_part, humanize_bytes


def register_handlers(bot: telebot.TeleBot):
    
    @bot.callback_query_handler(lambda callback: callback.data.split()[0].lower() == 'start_stop')
    def start_stop_torrent(callback: telebot.types.CallbackQuery):
        tid = callback.data.split()[1]
        try:
            torrent = transmission.get_torrent(tid)
        except KeyError:
            bot.send_message(callback.message.chat.id, f'Торрент #{tid} не существует!')
            return

        status_code = torrent._fields['status'].value
        to_start_torrent = status_code == TorrentStatus.STOPPED.value

        if to_start_torrent:
            torrent.start()
            bot.answer_callback_query(callback.id, m.TORRENT_STARTED(tid))
        else:
            torrent.stop()
            bot.answer_callback_query(callback.id, m.TORRENT_STOPPED(tid))

        def update_status():
            start_time = time.time()
            while time.time() < start_time + 4:
                torrent = transmission.get_torrent(tid)
                text, markup = render_status_message(torrent)
                if text != callback.message.text:
                    bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id,
                                          reply_markup=markup)
                    return
                time.sleep(0.3)
            msg = m.FAILED_TO_START if to_start_torrent else m.FAILED_TO_STOP
            bot.send_message(callback.message.chat.id, msg)

        # Asynchronously update the message
        scheduler.add_job(update_status)


    @bot.callback_query_handler(lambda callback: callback.data.split()[0].lower() == 'refresh')
    def refresh_torrent_status(cb: telebot.types.CallbackQuery):
        tid = cb.data.split()[1]
        torrent = transmission.get_torrent(torrent_id=tid)
        text, markup = render_status_message(torrent)

        if cb.message.text == text:
            bot.answer_callback_query(cb.id, m.REFRESH_UP_TO_DATE)
            return

        bot.edit_message_text(text,
                              chat_id=cb.message.chat.id,
                              message_id=cb.message.message_id,
                              reply_markup=markup)
        bot.answer_callback_query(cb.id, m.REFRESH_OK)

    @bot.callback_query_handler(lambda callback: callback.data.split()[0].lower() == 'remove')
    def remove_torrent(callback):
        tid = callback.data.split()[1]
        bot.send_message(callback.message.chat.id, m.REMOVE_CONFIRMATION(tid),
                         reply_markup=get_inline_confirm_removing_markup(tid))

    @bot.callback_query_handler(lambda cb: cb.data == CallbackCommands.CANCEL_MULTI_STEP_ACTION)
    def cancel_multi_step_command(cb: telebot.types.CallbackQuery):
        if cb.message.chat.id in bot.next_step_handlers.keys():
            del bot.next_step_handlers[cb.message.chat.id]
        bot.delete_message(cb.message.chat.id, cb.message.message_id)

    @bot.callback_query_handler(lambda cb: cb.data.startswith('confirm_removing'))
    def confirm_removing(callback):
        answer, tid, expire_timestamp = callback.data.split()[1:]

        if time.time() > float(expire_timestamp):
            bot.send_message(callback.message.chat.id, m.REMOVE_LINK_EXPIRED)
            return

        if answer == 'torrent_only':
            transmission.remove_torrent(tid, delete_data=False)
            bot.send_message(callback.message.chat.id, m.TORRENT_REMOVED(tid))
        elif answer == 'torrent_and_data':
            transmission.remove_torrent(tid, delete_data=True)
            bot.send_message(callback.message.chat.id, m.TORRENT_AND_DATA_REMOVED(tid))
        else:
            bot.send_message(callback.message.chat.id, m.ERROR_INVALID_ANSWER)
            raise ValueError('Invalid data in remove confirmation.')

        bot.delete_message(callback.message.chat.id, callback.message.message_id)

    @bot.callback_query_handler(lambda cb: cb.data == 'extra_actions')
    def show_exta_actions(cb: telebot.types.CallbackQuery):
        bot.edit_message_reply_markup(cb.message.chat.id, cb.message.message_id, reply_markup=extra_actions_markup)

    @bot.callback_query_handler(lambda cb: cb.data.split()[0].lower() == 'files')
    def show_files(callback):
        origin_msg: telebot.types.Message = callback.message
        tid = parse_tid_from_status_message(origin_msg.text)

        files = transmission.get_files(tid)[int(tid)]
        for file_id in files:
            files[file_id]['file_id'] = file_id

        files_dict = paths_to_dict(files)

        with shelve.open(config.SHELVENAME) as db:
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

        with shelve.open(config.SHELVENAME) as db:
            db[f'{callback.message.chat.id}_file_message_id'] = msg.message_id

    @bot.callback_query_handler(lambda cb: cb.data.split()[0].lower() == 'go_to')
    def go_to_files(callback):
        cb_splitted = callback.data.split()
        tid = cb_splitted[1]

        hexhash = cb_splitted[2]
        # go_to = ' '.join(cb_splitted[2:]) if len(cb_splitted) > 2 else None    # None in case when we return to root

        with shelve.open(config.SHELVENAME) as db:
            files_dict = db[f'{callback.message.chat.id}_files_dict']
            shelved_tid = db[f'{callback.message.chat.id}_files_tid']

            # Unhashing go_to path
            go_to = db[f'{callback.message.chat.id}_hash_aliases'][hexhash]
            if go_to == '':
                go_to = None

        if shelved_tid != tid:
            # Interaction with old file browser
            bot.send_message(callback.message.chat.id, m.FILE_BROWSER_EXPIRED)
            return

        if go_to is not None:
            files_subdict = files_dict_part(files_dict, path=go_to)

            if 'file_id' in files_subdict and isinstance(files_subdict['file_id'], int):
                # Clicking on file
                bot.answer_callback_query(callback.id, m.CLICKING_FILE, show_alert=False)
                return

        markup = get_inline_files_markup(tid=tid, files_dict=files_dict, current_position=go_to)
        bot.edit_message_reply_markup(callback.message.chat.id, message_id=callback.message.message_id,
                                      reply_markup=markup)

    @bot.callback_query_handler(lambda cb: cb.data.startswith('check ') or cb.data.startswith('uncheck '))
    def check_files(callback):
        action, tid, hexhash = callback.data.split()

        with shelve.open(config.SHELVENAME) as db:
            path = db[f'{callback.message.chat.id}_hash_aliases'][hexhash]

        feed = {
            tid: {}
        }

        files = transmission.get_files(tid)[int(tid)]
        file_ids = [file_id for file_id in files if files[file_id]['name'].startswith(path)]

        for file_id in file_ids:
            feed[tid][file_id] = {
                'selected': True if action == 'check' else False
            }

        transmission.set_files(feed)

        if action == 'check':
            bot.send_message(callback.message.chat.id, m.FILES_MARKED(tid=tid, path=path))
        else:
            bot.send_message(callback.message.chat.id, m.FILES_UNMARKED(tid=tid, path=path))

    @bot.callback_query_handler(lambda cb: cb.data == ExtraActions.BACK_TO_MAIN)
    def back_to_main_actions(cb: telebot.types.CallbackQuery):
        origin_msg: telebot.types.Message = cb.message
        tid = origin_msg.text[:origin_msg.text.find(')')]
        main_markup = get_inline_action_markup(tid)
        bot.edit_message_reply_markup(cb.message.chat.id, cb.message.message_id, reply_markup=main_markup)

    @bot.callback_query_handler(lambda cb: cb.data == ExtraActions.SET_LOCATION)
    def set_torrent_location(cb: telebot.types.CallbackQuery):
        origin_msg: telebot.types.Message = cb.message
        tid = parse_tid_from_status_message(origin_msg.text)
        # Reset torrent tool panel to main
        main_markup = get_inline_action_markup(tid)
        bot.edit_message_reply_markup(cb.message.chat.id, cb.message.message_id, reply_markup=main_markup)

        bot.send_message(origin_msg.chat.id, m.ENTER_NEW_PATH, reply_markup=cancel_markup)
        bot.register_next_step_handler(origin_msg, read_new_torrent_location, tid=tid)

    def read_new_torrent_location(message: telebot.types.Message, tid: Union[str, int]):
        path = message.text.strip()
        torrent = transmission.get_torrent(torrent_id=tid)
        try:
            free_space = transmission.free_space(path)
        except transmissionrpc.TransmissionError:
            bot.send_message(message.chat.id, m.LOCATION_SET_FAILED)
            return

        if free_space < torrent.sizeWhenDone:
            bot.send_message(message.chat.id,
                             m.NOT_ENOUGH_SPACE(humanize_bytes(torrent.sizeWhenDone), humanize_bytes(free_space)))
            return

        try:
            torrent.locate_data(path)
        except transmissionrpc.TransmissionError:
            bot.send_message(message.chat.id, m.LOCATION_SET_FAILED)
            return

        bot.send_message(message.chat.id, m.LOCATION_SET_OK)