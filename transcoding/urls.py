from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'transcoding.views.tq_ls'),
#    (r'^(?P<the_id>\d+)/$', 'transcoding.views.tq'),
    (r'^ls/(?P<path>.*)$', 'transcoding.views.chdir'),
    (r'^ls/$', 'transcoding.views.chdir'),
    (r'^add/$', 'transcoding.views.add'),
    (r'^add_files/$', 'transcoding.views.file'),
)
