from django.conf.urls.defaults import *
from django.contrib.sitemaps import FlatPageSitemap
from django.views.generic.simple import direct_to_template

from tagging.views import tagged_object_list

from sitemaps import TopicSiteMap

sitemaps = {
    'site': TopicSiteMap,
    'flat': FlatPageSitemap,
}

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'index.html'}),
    (r'^search-results/$', 'fs.views.search'),
    (r'^subscribe/$', 'fs.views.subscribtion'),
    (r'^tnx/(?P<the_id>\d+)/$', 'fs.views.tnx'),
    (r'^torrent/(?P<the_id>\d+)/$', 'fs.views.get_torrent'),
    (r'^contact/$', 'contacts.views.contact'),
    (r'^contact/thanks/$', direct_to_template, {'template': 'contacts/thanks.html'}),
    (r'^bbs/', include('board.urls')),
    (r'^comments/$', include('django.contrib.comments.urls')),
    (r'^comments/post/$', 'fs.views.comment'),
    (r'^rate/$', 'fs.views.rate'),
    (r'^xmltags/(?P<section>\w+)/$', 'fs.views.xml_tags'),
    (r'^xmltags/(?P<section>\w+)/page-(?P<page>[\d]+)/$', 'fs.views.xml_tags'),
    (r'^edit/(?P<the_id>\d+)/$', 'fs.views.edit'),
    (r'^add/$', 'fs.views.new'),
    (r'^tq/', include('transcoding.urls')),

    (r'^login/$', 'users.views.login'),
    (r'^auth/$', 'users.views.auth'),
    (r'^logout/$', 'users.views.logout'),
    (r'^self/$', 'users.views.edit_profile'),
    (r'^self/openid/$', 'users.views.change_openid'),
    (r'^self/openid_complete/$', 'users.views.change_openid_complete'),
    (r'^self/personal/$', 'users.views.post_personal'),
    (r'^self/hcard/$', 'users.views.read_hcard'),
    (r'^chpw/$', 'users.views.chpw',
	{'template_name': 'users/chpw.html'}),
    (r'^chpw/(?P<key>\w+)/$', 'users.views.chpw',
	{'template_name': 'users/chpw.html'}),
    (r'^chpw_urlsent/$', direct_to_template,
	{'template': 'users/chpw_email_sent.html'}),
    (r'^chpw_done/$', 'users.views.chpw_done',
	{'template_name': 'users/chpw_done.html'}),
    (r'^signup/$', 'users.views.register'),
    (r'^signup/complete/$', direct_to_template,
	{'template': 'users/registration_complete.html'}),
    (r'^activate/(?P<activation_key>\w+)/$', 'users.views.activate'),

    (r'^leave_message/$', 'users.views.leave_message'),
    (r'^leave_message/(?P<the_id>\d+)/$', 'users.views.leave_message'),
    (r'^messages/(?P<action>[-\w]+)/$', 'users.views.messages'),
    url(r'^sections/$', direct_to_template, { 'template': 'sections_index.html' }),

    url(r'^sections/(?P<slug>[-\w]+)/$', 'fs.views.topic_list', name='by_section'),

    url(r'^tag/(?P<tag>[^/]+)/$', 'fs.views.tags', name='by_tag'),

    (r'^~(?P<username>[-\w]+)/$', 'fs.views.topic'),
    (r'^~(?P<username>[-\w]+)/(?P<slug>[-\w]+)/$', 'fs.views.topic'),

    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
	{'packages': 'django.conf'}),

    (r'^admin/', include('admin.urls')),
    (r'^feeds/', include('feed.urls')),
    (r'^announce', 'tracker.views.announce'),
    (r'^scrape', 'tracker.views.scrape'),

    url(r'^sitemap.xml$', 'django.contrib.sitemaps.views.sitemap',
	{'sitemaps': sitemaps}),
    (r'^upload_scr/(?P<the_id>[\d]+)/$', 'fs.views.upload_scr'),
)
