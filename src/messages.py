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
    BACK = 'Назад'

    NO_TORRENTS = 'Список торрентов пуст.'
    LINK_NOT_FOUND_IN_DB = 'Ссылка не найдена в базе данных.'
    CANNOT_SEARCH = 'Поиск по трекеру не удался. Проверьте доступность трекера.'

    TORRENT_STARTED = staticmethod(lambda tid: f'Запуск торрента #{tid}...')
    TORRENT_STOPPED = staticmethod(lambda tid: f'Остановка торрента #{tid}...')
    FAILED_TO_START = 'Не удалось запустить торрент!'
    FAILED_TO_STOP = 'Не удалось остановить торрент!'

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

    # --- Extra actions ---
    SET_LOCATION_BUTTON = '📁 Изменить расположение'
    ENTER_NEW_PATH = 'Введите новый путь торрента'
    LOCATION_SET_FAILED = 'Не удалось изменить путь скачивания. Проверьте корректность пути.'
    NOT_ENOUGH_SPACE = staticmethod(lambda size, space: f'Недостаточно свободного места по указанному пути.\n'
                                                        f'Необходимо: {size}\n'
                                                        f'Свободно: {space}')
    LOCATION_SET_OK = 'Переносим файлы торрента.'
