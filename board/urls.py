from django.conf.urls.defaults import *
from django.contrib.auth.models import User
from django.views.generic.simple import direct_to_template

from board.feeds import LatestPosts
from board.rpc import rpc_post, rpc_lookup, rpc_preview, rpc_ban
from board.views import *

feeds = {'latest': LatestPosts}

js_info_dict = {
    'packages': ('board',),
}

urlpatterns = patterns('',
    (r'^$', thread_index, {}, 'board_index'),
    (r'search-results/$', search),
    (r'feedback/sent/$', direct_to_template, {'template': 
        'board/feedback_sent.html'}),

    (r'^private/$', private_index, {}, 'board_private_index'),
    (r'^categories/$', category_index, {}, 'board_category_index'),
    (r'^favorites/$', favorite_index, {}, 'board_favorite_index'),
    (r'^edit_post/(?P<original>\d+)/$', edit_post, {}, 'board_edit_post'),
    (r'^threads/$', thread_index, {}, 'board_thread_index'),
    (r'^threads/id/(?P<thread_id>\d+)/$', thread, {}, 'board_thread'),
    (r'^threads/category/(?P<cat_id>\d+)/$', category_thread_index, {}, 'board_category_thread_index'),
    (r'^threads/category/(?P<cat_id>\d+)/newtopic/$', new_thread, {}, 'board_new_thread'),
    (r'^threads/post/(?P<post_id>\d+)/$', locate_post, {}, 'board_locate_post'),
    (r'^settings/$', edit_settings, {}, 'board_edit_settings'),

    # Groups
    (r'^groups/(?P<group_id>\d+)/manage/$', manage_group, {}, 'board_manage_group'),
    (r'^groups/(?P<group_id>\d+)/invite/$', invite_user_to_group, {}, 'board_invite_user_to_group'),
    (r'^groups/(?P<group_id>\d+)/remuser/$', remove_user_from_group, {}, 'board_remove_user_from_group'),
    (r'^groups/(?P<group_id>\d+)/grant_admin/$', grant_group_admin_rights, {}, 'board_grant_group_admin_rights'),

    (r'^del_thread/(?P<the_id>\d+)/$', 'board.views.del_thread'),

    # Invitations
    (r'invitations/(?P<invitation_id>\d+)/discard/$', discard_invitation, {}, 'board_discard_invitation'),
    (r'invitations/(?P<invitation_id>\d+)/answer/$', answer_invitation, {}, 'board_answer_invitation'),
    

    # RPC
    (r'^rpc/action/$', rpc, {}, 'board_rpc_action'),
    (r'^rpc/postrev/$', rpc_post, {}, 'board_rpc_postrev'),
    (r'^rpc/preview/$', rpc_preview, {}, 'board_rpc_preview'),
    (r'^rpc/user_lookup/$', rpc_lookup,
            {
                'queryset':User.objects.all(),
                'field':'username',
            }, 'board_rpc_user_lookup'
        ),
    (r'^rpc/ban/$', rpc_ban),

    # feeds
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}, 'board_feeds'),

    # javascript translations
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict, 'board_js_i18n'),
)
