#!/usr/bin/python
# removes users which authenticated by openid and have no posts
import sys
sys.path.append('/home/grey/src/df')
from users.models import User
user_lst = User.objects.all()
for u in user_lst:
    if u.is_staff or u.is_superuser:
	continue
    if u.email == u'user@nowhere':
	if u.attrs.has_key('posts'):
	    if u.attrs['posts']:
		continue
	u.delete()
	print u.username, "deleted"
