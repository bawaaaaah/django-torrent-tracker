from django.conf.urls.defaults import *
from board.models import Forum

info_dict = {
    'queryset': Forum.objects.order_by('ordering'),
}

urlpatterns = patterns('',
    (r'^$', 'board.views.thread_index'),
    (r'^newtopic/$', 'board.views.new_thread'),
    (r'^forums/$', 'django.views.generic.list_detail.object_list', info_dict),
    (r'^topics/(?P<slug>[-\w]+)/$', 'board.views.thread'),
    (r'^rpc/(?P<action>[-\w]+)/(?P<the_id>\d+)/$', 'board.views.rpc'),
    (r'^rpc/preview/$', 'board.views.preview'),
    (r'^(?P<forum_slug>[-\w]+)/$', 'board.views.thread_index'),
)
