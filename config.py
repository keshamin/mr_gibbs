from ast import literal_eval
import os
from dotenv import load_dotenv


ENV_PREFIX = 'MR_G_'
CONFIG_ENV_FILE = 'config.env'


def prefixed(var_name):
    return ENV_PREFIX + var_name


# Loading configuration from env-file
app_dir = os.path.dirname(os.path.abspath(__file__))
if CONFIG_ENV_FILE in os.listdir():
    load_dotenv(os.path.join(app_dir, CONFIG_ENV_FILE))


# Reading configuration from ENV
TOKEN = os.environ.get(prefixed('TOKEN'))

WEBHOOK_URL_BASE = os.getenv('WEBHOOK_URL_BASE')
WEBHOOK_URL_PATH = os.getenv('WEBHOOK_URL_PATH')
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST') or '0.0.0.0'
WEBHOOK_PORT = os.getenv('WEBHOOK_PORT') or 80

ADMIN_ID = int(os.environ.get(prefixed('ADMIN_ID')))
USERS_IDS = literal_eval(os.environ.get(prefixed('USERS_IDS'), default='[]'))

TRANS_HOST = os.environ.get(prefixed('TRANS_HOST'))
TRANS_PORT = os.environ.get(prefixed('TRANS_PORT'))
TRANS_USER = os.environ.get(prefixed('TRANS_USER'))
TRANS_PASSWORD = os.environ.get(prefixed('TRANS_PASSWORD'))

CATEGORIES_LAYOUT = literal_eval(os.environ.get(prefixed('CATEGORIES')))

if isinstance(CATEGORIES_LAYOUT, dict):
    CATEGORIES_LAYOUT = [{category: path} for category, path in CATEGORIES_LAYOUT.items()]

CATEGORIES = {category: path for row in CATEGORIES_LAYOUT for category, path in row.items()}

SHELVENAME = os.environ.get(prefixed('SHELVENAME'), default='db.shelve')

TRACKER = os.environ.get(prefixed('TRACKER'), default='http://rutor.info')

REMOVE_DIALOG_TIMEOUT = int(os.environ.get(prefixed('REMOVE_DIALOG_TIMEOUT'), default=120))

DEBUG = bool(os.environ.get('DEBUG', default=False))
