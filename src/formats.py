from typing import Tuple, Union

from transmissionrpc import Torrent
import telebot

from markups import get_inline_action_markup
from transmission_utils import status_to_emoji


def render_status_message(torrent: Torrent) -> Tuple[str, telebot.types.InlineKeyboardMarkup]:
    torrent_template = '{tid}) {status_emoji} {name} ({percent}%)'
    tid = torrent.id
    status_emoji = status_to_emoji[torrent.status]
    text = torrent_template.format(tid=tid, name=torrent.name,
                                   status_emoji=status_emoji, percent=int(torrent.progress))
    markup = get_inline_action_markup(tid)
    return text, markup


def parse_tid_from_status_message(msg: str) -> int:
    return int(msg[:msg.find(')')])
