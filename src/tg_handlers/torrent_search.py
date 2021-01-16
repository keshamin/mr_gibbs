import shelve

from telebot import TeleBot

import config
from init import m
from markups import inline_arrows_markup
from utils import get_search_results, prepare_response_list


def register_handlers(bot: TeleBot):

    @bot.callback_query_handler(lambda callback: callback.data.lower() in ('left', 'right'))
    def turn_page(cb):
        if cb.data.lower() == 'left':
            k = -1
        elif cb.data.lower() == 'right':
            k = 1
        with shelve.open(config.SHELVENAME) as db:
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


def rutor_search(bot, chat_id, search_request):
    try:
        results_list = get_search_results(search_request)
    except ValueError as e:
        bot.send_message(chat_id, m.CANNOT_SEARCH)
        raise e

    with shelve.open(config.SHELVENAME) as db:
        db[f'{chat_id}_search_results'] = results_list
        db[f'{chat_id}_search_cursor'] = 0
    first_five = results_list[:5]
    response = prepare_response_list(first_five, start=0)

    if len(response) > 0:
        bot.send_message(chat_id, response, reply_markup=inline_arrows_markup)
    else:
        bot.send_message(chat_id, m.NOT_FOUND_ON_TRACKER(search_request))
