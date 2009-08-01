import os, sys
apache_configuration= os.path.dirname(__file__)

PROJECT_BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = os.path.basename(PROJECT_BASE)
SITE_BASE = PROJECT_BASE
sys.path.append(SITE_BASE)
sys.path.append(PROJECT_BASE)
os.environ['PYTHON_EGG_CACHE'] = os.path.join(SITE_BASE, '.python-eggs')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
