from django.conf.urls.defaults import *
from admin.views import *
import settings
from django.views.generic.simple import direct_to_template

if settings.USE_I18N:
    i18n_view = 'django.views.i18n.javascript_catalog'
else:
    i18n_view = 'django.views.i18n.null_javascript_catalog'

urlpatterns = patterns('',
    (r'^$', direct_to_template, { 'template': 'admin/index.html' }),
    (r'^delete/(?P<name>\w+)/(?P<the_id>\d+)/$', delete),
    (r'^edit/(?P<name>\w+)/(?P<the_id>\d+)/$', edit),
    (r'^approve/(?P<the_id>\d+)/$', approve),
    (r'^jsi18n/$', i18n_view, {'packages': 'django.conf'}),
    (r'^(?P<name>\w+)/$', items),
    (r'^(?P<name>\w+)/page-(?P<page>[\d]+)/$', items),
)
