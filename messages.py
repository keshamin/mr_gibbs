from random import choice


class M(object):
    def __getattribute__(self, item):
        attr = super().__getattribute__(item)
        if isinstance(attr, tuple):
            return choice(attr)
        return attr

    YES = 'Да'
    NO = 'Нет'
    CANCEL = 'Отмена'

    NO_TORRENTS = 'Список торрентов пуст.'
    LINK_NOT_FOUND_IN_DB = 'Ссылка не найдена в базе данных.'

    @staticmethod
    def TORRENT_STARTED(tid):
        return 'Торрент #{} был запущен.'.format(tid)

    @staticmethod
    def TORRENT_STOPPED(tid):
        return 'Торрент #{} был остановлен.'.format(tid)

    # --- Removing torrent ---
    @staticmethod
    def REMOVE_CONFIRMATION(tid):
        return 'Вы уверены, что хотите удалить торрент #{}?'.format(tid)

    REMOVE_TORRENT_ONLY = 'Торрент'
    REMOVE_TORRENT_AND_DATA = 'Торрент и данные'

    @staticmethod
    def TORRENT_REMOVED(tid):
        return 'Торрент #{} был удален.'.format(tid)

    @staticmethod
    def TORRENT_AND_DATA_REMOVED(tid):
        return 'Торрент #{} и скачанные файлы удалены'.format(tid)

    NOT_REMOVING = ('Без проблем.', 'Оставляем все как есть.')
    REMOVE_LINK_EXPIRED = 'Время жизни ссылки истекло'
    ERROR_INVALID_ANSWER = '⚠️ Ошибка сервера: Некорректный ответ!'

    # --- Files ---
    FILE_BROWSER_EXPIRED = 'Время жизни кнопки истекло'
    CLICKING_FILE = 'Это конечный файл.'

    @staticmethod
    def FILES_MARKED(tid, path):
        return '{} в торренте #{} скачивается'.format(path, tid)

    @staticmethod
    def FILES_UNMARKED(tid, path):
        return '{} в торренте #{} не скачивается'.format(path, tid)

    # --- Tracker Search ---
    @staticmethod
    def NOT_FOUND_ON_TRACKER(query):
        return f'По запросу {query} ничего не найдено.'
