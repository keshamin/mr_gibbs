from telebot import TeleBot
from . import main_menu, torrent_search, common, add_torrent, download_torrent_file, manage_torrents


def register_handlers(bot: TeleBot):
    handler_modules = [
        common,
        main_menu,
        manage_torrents,
        torrent_search,
        add_torrent,
        download_torrent_file,
    ]

    for module in handler_modules:
        module.register_handlers(bot)
