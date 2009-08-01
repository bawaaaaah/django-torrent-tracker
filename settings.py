# Django settings for dc project.

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Dorian Grey', 'grey@0x2a.com.ua'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = ''           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = ''             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Etc/GMT+2'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'ru'

DEFAULT_CHARSET = 'utf-8'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'im1i$8xve2yyuuvq3z(az_20eov-ghazwptnsu5h_00ua@$%s0'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'board.middleware.threadlocals.ThreadLocals',
    # These are optional
    'board.middleware.ban.IPBanMiddleware',
    'board.middleware.ban.UserBanMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), 'templates')
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.comments',
    'django.contrib.flatpages',
    'django.contrib.humanize',
    'users',
    'tagging',
    'fs',
    'contacts',
    'board',
    'tracker',
    'stats',
    'transcoding',
    'board',
)

FTP_HOMEDIR = '/mnt/dfs'
#must be writable by www server
OPENID_STORE_ROOT = os.path.join(os.path.dirname(__file__), 'store')
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'users.util.EmailBackend',
    'users.util.OpenIdBackend',
)
# if not specified, the result of auth request will be applied to the whole site
OPENID_TRUST_URL = ''
ACCOUNT_ACTIVATION_DAYS = 5
PWD_CHANGE_EXPIRATION_DAYS = 1
ACTIVATION_ENABLED = False #True by default
LOGIN_URL = "/login/"

FORCE_LOWERCASE_TAGS = True

#from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.i18n',
    'context_processors.global_tracker_settings',
)
CACHE_BACKEND = 'file://%s'%os.path.join(os.path.dirname(__file__), 'store', 'cache')
RESULTS_ON_PAGE = 50
ORPHANS = 5
BBS_RESULTS_ON_PAGE = 80
BBS_ORPHANS = 10

EMAIL_HOST = '127.0.0.1'
#RECAPTCHA_PUB_KEY = "6LcoHgAAAAAAAAOwnf3YF8TAu2gdwhaQLjBD2g_G"
RECAPTCHA_PUB_KEY = "6LcoHgAAAAAAAAOwnf3YF8TAu2gdwhaQLjBD2g_G"
#RECAPTCHA_PRIVATE_KEY = "6LcoHgAAAAAAAHZrG7PRZTWF3HW5Oni5QMjHW9Fw"
RECAPTCHA_PRIVATE_KEY = "6LcoHgAAAAAAAHZrG7PRZTWF3HW5Oni5QMjHW9Fw"
BANNED_IPS = []
SCRAPE_URL = 'http://127.0.0.1/scrape'
ANNOUNCE_URL = 'http://127.0.0.1/announce'

# Should we require a certain announce protocol?
# "standard" allows all protocols
# "no_peer_id" allows only no_peer_id and compact
# "compact" allows only compact
REQUIRE_ANNOUNCE_PROTOCOL = "standard"
# announcements per minute
MAX_ANNOUNCE_RATE = 500
# peers should wait at least this many seconds between announcements
MIN_ANNOUNCE_INTERVAL = 900
# consider a peer dead if it has not announced in a number of seconds equal
# to this many times the calculated announce interval at the time of its last
# announcement (must be greater than 1; recommend 1.2)
EXPIRE_FACTOR = 1.2
# peers should wait at least this many times the current calculated announce
# interval between scrape requests
SCRAPE_FACTOR = 0.5

NUMBER_OF_POSTS_PER_DAY = 4

MEMCACHE = '127.0.0.1:11211'

SEARCH_CRAWLERS = (
    "search.crawlers.models.ModelCrawler",
)

# I don't want to store this in db
SITE_DOMAIN = '0xdf.net'
SITE_NAME = '0xdf'

FILE_UPLOAD_TEMP_DIR = os.path.join(os.path.dirname(__file__), 'store', 'temp')

OPEN_TRACKER = True
SOLR_URL = 'http://127.0.0.1:8080/solr/'

# if CENSORSHIP == True, then 
# * user will be unable to change post when it is approved
# * all new posts will not appear on first page if not approved

CENSORSHIP = False
