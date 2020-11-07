from typing import Union

from telebot import types
import shelve
import hashlib
from time import time
from collections import OrderedDict

from config import ADMIN_ID, SHELVENAME, REMOVE_DIALOG_TIMEOUT, CATEGORIES_LAYOUT
from messages import M
import os

from utils import files_dict_part, calc_selected_set

main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
main_markup.add(*[types.KeyboardButton(text) for text in ('Торренты ↕️', 'Поиск 🔍')])

category_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
category_markup.add(*[types.KeyboardButton(text) for text in ('Movie', 'TV', 'Other')])

action_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
action_markup.add(*[types.KeyboardButton(text) for text in ('Start', 'Stop', 'Remove')])

yes_no_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
yes_no_markup.add(*[types.KeyboardButton(text) for text in ('Да', 'Нет')])

inline_yes_no_markup = types.InlineKeyboardMarkup()
inline_yes_no_markup.add(*[types.InlineKeyboardButton(text=text, callback_data=data) for text, data in
                           (('Да', 'yes'), ('Нет', 'no'))])

inline_arrows_markup = types.InlineKeyboardMarkup()
inline_arrows_markup.row(*[types.InlineKeyboardButton(
    text=arrow, callback_data=text) for arrow, text in [('⬅️', 'left'), ('➡️', 'right')]]
                         )
inline_arrows_markup.row(types.InlineKeyboardButton(text='Не запускать', callback_data='dont_start'))


inline_file_browser_expired_markup = types.InlineKeyboardMarkup()
inline_file_browser_expired_markup.add(types.InlineKeyboardButton(text=M.FILE_BROWSER_EXPIRED, callback_data='null'))


def get_inline_category_markup(uid):
    markup = types.InlineKeyboardMarkup()
    for categories_row in CATEGORIES_LAYOUT:
        markup.row(*[types.InlineKeyboardButton(
            text=category, callback_data='{} {}'.format(category, uid)) for category in categories_row.keys()
        ])
    markup.row(types.InlineKeyboardButton(text='Скачать .torrent 💾', callback_data='download_torrent'))
    return markup


def get_inline_action_markup(tid):
    markup = types.InlineKeyboardMarkup(row_width=4)

    action_emoji = OrderedDict([
        ('start_stop', '⏯'),
        ('files', '📂'),
        ('remove', '🗑'),
    ])
    markup.add(
        *[types.InlineKeyboardButton(text=emoji, callback_data='{} {}'.format(action, tid))
          for action, emoji in action_emoji.items()],
        types.InlineKeyboardButton(text='⚙️', callback_data='extra_actions')
    )
    return markup


class ExtraActions:
    SET_LOCATION = 'set_location'
    BACK_TO_MAIN = 'back_to_main'


def build_extra_actions_markup() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)

    extra_actions = {
        M.SET_LOCATION_BUTTON: ExtraActions.SET_LOCATION
    }

    for label, data in extra_actions.items():
        markup.add(types.InlineKeyboardButton(text=label, callback_data=data))

    markup.add(types.InlineKeyboardButton(text=M.BACK, callback_data=ExtraActions.BACK_TO_MAIN))

    return markup


def get_inline_files_markup(tid, files_dict, current_position=None, chat_id=ADMIN_ID):

    markup = types.InlineKeyboardMarkup(row_width=2)

    files_subdict = files_dict_part(files_dict, path=current_position) if current_position else files_dict

    for item in files_subdict:
        path = '{}/{}'.format(current_position, item) if current_position is not None else item
        hexhash = hashlib.md5(path.encode()).hexdigest()
        with shelve.open(SHELVENAME) as db:
            aliases_dict = db[f'{chat_id}_hash_aliases']
            aliases_dict[hexhash] = path
            db[f'{chat_id}_hash_aliases'] = aliases_dict

        if 'file_id' in files_subdict[item] and isinstance(files_subdict[item]['file_id'], int):
            dir_file_icon = '📄'
            tick_icon = '☀️' if files_subdict[item]['selected'] else '❄️'
        else:
            dir_file_icon = '📦'
            selected_set = calc_selected_set(files_subdict[item])
            if len(selected_set) == 1:
                tick_icon = '☀️' if True in selected_set else '❄️'
            else:
                tick_icon = '⛅️'

        markup.row(types.InlineKeyboardButton(text='{} {} {}'.format(dir_file_icon, tick_icon, item),
                                              callback_data='go_to {} {}'.format(tid, hexhash)))
        markup.row(
            types.InlineKeyboardButton(text='☀️', callback_data='check {} {}'.format(tid, hexhash)),
            types.InlineKeyboardButton(text='❄️', callback_data='uncheck {} {}'.format(tid, hexhash))
        )

    if current_position is not None:
        path = os.path.dirname(current_position)

        hexhash = hashlib.md5(path.encode()).hexdigest()
        with shelve.open(SHELVENAME) as db:
            aliases_dict = db[f'{chat_id}_hash_aliases']
            aliases_dict[hexhash] = path
            db[f'{chat_id}_hash_aliases'] = aliases_dict

        markup.row(types.InlineKeyboardButton(text='Назад', callback_data='go_to {} {}'.format(tid, hexhash)))

    return markup


def get_inline_confirm_removing_markup(tid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for answer, text in {'torrent_only': M.REMOVE_TORRENT_ONLY,
                         'torrent_and_data': M.REMOVE_TORRENT_AND_DATA,
                         'cancel': M.CANCEL}.items():
        markup.add(types.InlineKeyboardButton(
            text=text,
            callback_data='confirm_removing {} {} {}'.format(answer, tid, time() + REMOVE_DIALOG_TIMEOUT))
        )
    return markup


extra_actions_markup = build_extra_actions_markup()
