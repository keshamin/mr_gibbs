from telebot import TeleBot

from config import TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASSWORD
from markups import main_markup
from messages import M
from trans import Trans


class SmartHomeBot(TeleBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.trans = Trans(TRANS_HOST, TRANS_PORT, user=TRANS_USER, password=TRANS_PASSWORD)
        self.M = M()
        self.memory = {}

        self.start_on_add = True

        # This dict converts Transmission status codes into emoji
        self.status_to_emoji = {
            0: '⛔️',    # 'stopped'
            1: '💬',     # check pending',
            2: '💬',     # 'checking',
            3: '💬',     # 'download pending',
            4: '⏬',      # 'downloading',
            5: '💬',     # 'seed pending',
            6: '✅',     # 'seeding',
        }

    def send_message(self, *args, reply_markup=main_markup, **kwargs):
        return super().send_message(*args, reply_markup=reply_markup, **kwargs)

    def file_ids_by_path(self, tid, path):
        files = self.trans.get_files(tid)[int(tid)]
        file_ids = [file_id for file_id in files if files[file_id]['name'].startswith(path)]

        return file_ids
