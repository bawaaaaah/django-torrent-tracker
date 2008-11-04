from openid.consumer.consumer import Consumer, SUCCESS
from django.contrib.auth.backends import ModelBackend
from django.forms.fields import email_re
from openid.store.filestore import FileOpenIDStore
from django.conf import settings
from django.forms.util import ValidationError

from users.models import User

def get_consumer(session):
    if not settings.OPENID_STORE_ROOT:
	raise Exception('OPENID_STORE_ROOT is not set')
    return Consumer(session, FileOpenIDStore(settings.OPENID_STORE_ROOT))

class OpenIdBackend(object):
    def authenticate(self, session=None, query=None, return_to=''):
	query = dict([(k, v) for k, v in query.items()])
	consumer = get_consumer(session)
	info = consumer.complete(query, return_to)
	if info.status != SUCCESS:
	    return None
	try:
	    user = User.objects.get(openid=info.identity_url)
	    if user.is_active == False:
		if user.attrs.has_key('reason'):
		    if user.attrs['reason']:
			raise ValidationError("Banned: '%s'"%user.attrs['reason'])
		raise ValidationError(_('Your account has been locked!'))
	except User.DoesNotExist:
	    import md5
	    from datetime import datetime
	    unique = md5.new(info.identity_url + str(datetime.now())).hexdigest()[:30]
	    user = User.objects.create_user('%s' % unique, 'user@nowhere', User.objects.make_random_password())
	    user.openid = info.identity_url
	    user.openid_server = info.endpoint.server_url
	    user.save()
	return user

    def get_user(self, user_id):
	try:
	    return User.objects.get(pk=user_id)
	except User.DoesNotExist:
	    return None

class EmailBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
	if email_re.search(username):
	    try:
		user = User.objects.get(email=username)
		if user.is_active == False:
		    if user.attrs.has_key('reason'):
			if user.attrs['reason']:
			    raise ValidationError("Banned: '%s'"%user.attrs['reason'])
		    raise ValidationError(_('Your account has been locked!'))
		if user.check_password(password):
		    return user
	    except User.DoesNotExist:
		return None
	return None


def login_without_password(request, user):
    from django.contrib.auth import load_backend
    import datetime
    user.last_login = datetime.datetime.now()
    user.save()
    backend = load_backend('django.contrib.auth.backends.ModelBackend')
    user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
    request.session['_auth_user_id'] = user.id
    request.session['_auth_user_backend'] = user.backend
    if hasattr(request, 'user'):
	request.user = user

