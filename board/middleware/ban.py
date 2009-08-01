from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.db.models import Q

from board.models import IPBan, UserBan

import datetime

class IPBanMiddleware(object):
    """
    Bans based on IP address.

    This middleware attempts to grab BANNED_IPS from the settings module.
    This variable holds a set of all the banned IP addresses, which is defined 
    in the database and automatically cached for efficiency.
    """

    def process_request(self, request):
        ip_address = request.META.get('REMOTE_ADDR', None)
        ban = IPBan.objects.filter(address=ip_address)
        if ban:
            return direct_to_template(request, 'board/banned_ip.html', {
                'reason': IPBan.objects.get(address=ip_address).reason
            })

class UserBanMiddleware(object):
    """
    Shows an error page to banned users and stop them from using the forum.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated():
            ban = UserBan.objects.filter(Q(expires__gt=datetime.datetime.now()
                )|Q(expires__isnull=True, user=request.user))
            if ban and hasattr(view_func, '_board'):
                return direct_to_template(request, 'board/banned_user.html', {
                    'ban': ban[0]
                })

