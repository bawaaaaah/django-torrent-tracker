from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_init
import re, datetime, sha, random
SHA1_RE = re.compile('^[a-f0-9]{40}$')
from django.conf import settings
from fields import Dict

def read_hcard(user_obj):
    """
    Searching for hCard on page that referrenced in openid.
    """
    from urllib2 import urlopen, URLError
    from BeautifulSoup import BeautifulSoup
    try:
	file = urlopen(user_obj.openid)
	content = file.read(512 * 1024)
    except (URLError, IOError):
	return
    soup = BeautifulSoup(content)
    vcard = soup.find(None, {'class': re.compile(r'\bvcard\b')})
    if vcard is None:
	return

    def _parse_property(class_name):
	el = vcard.find(None, {'class': re.compile(r'\b%s\b' % class_name)})
	if el is None:
	    return
	f = lambda:''.join([s for s in el.recursiveChildGenerator() if isinstance(s, unicode)])
	if el.name == u'abbr' and el.has_key('title'):
	    if el['title']:
		result = el['title']
	    else:
		result = f()
	else:
	    result = f()
	return result.replace('\n',' ').strip().encode(settings.DEFAULT_CHARSET)

    info = dict((n, _parse_property(n)) for n in ['nickname', 'fn'])
    if info.has_key('nickname'):
	user_obj.full_name = info['nickname']
    elif info.has_key('fn'):
	user_obj.full_name = info['fn']

def _user_pre_save(sender, instance, signal, *args, **kwargs):
    if instance.openid and not instance.full_name:
	read_hcard(instance)
    if not settings.OPEN_TRACKER:
        if not instance.passkey:
		instance.passkey = sha.new(str(datetime.datetime.now()) + str(random.randint(1, 1000000000)) + instance.username + instance.email).hexdigest()

def _add_attrs_and_methods(sender, instance, signal, *args, **kwargs):
    instance.attrs = Dict(instance)

User.add_to_class('full_name', models.CharField(max_length=200, null=True, blank=True))
User.add_to_class('title', models.CharField(max_length=255, null=True, blank=True, help_text=_("The preferred title for ~/, like the title for youtube channel")))
User.add_to_class('openid', models.CharField(max_length=200, null=True, unique=True))
User.add_to_class('openid_server', models.CharField(max_length=200, null=True))
User.add_to_class('birthday', models.DateField('birthday', null=True, blank=True))
User.add_to_class('im', models.CharField(max_length=200, blank=True, null=True))
User.add_to_class('image', models.CharField(blank=True, null=True, max_length=255))
User.add_to_class('text', models.TextField(blank=True, null=True))
if not settings.OPEN_TRACKER:
    User.add_to_class('passkey', models.CharField(max_length=40, blank=True, null=True))
User.add_to_class('prefs', models.TextField(blank=True, null=True))

def _get_age(self):
    if not self.birthday: return 0
    diff = datetime.date.today() - self.birthday
    days = diff.days
    return int(days/365.2425)
User.age = property(_get_age)

def _get_name(self):
    if self.first_name:
      return self.first_name
    elif self.openid:
      result = self.openid[self.openid.index('://') + 3:]
      try:
        if result.index('/') == len(result) - 1:
	  result = result[:-1]
      except ValueError:
        pass
      return result
    else:
      return unicode(self)
User.name = property(_get_name)

class RegistrationManager(models.Manager):
  """
  Custom manager for the ``RegistrationProfile`` model.
  The methods defined here provide shortcuts for account creation
  and activation (including generation and emailing of activation
  keys), and for cleaning out expired inactive accounts.
  """
  def activate_user(self, activation_key):
    """
    Validates an activation key and activates the corresponding
    ``User`` if valid.
    If the key is valid and has not expired, returns the ``User``
    after activating.
    If the key is not valid or has expired, returns ``False``.
    If the key is valid but the ``User`` is already active,
    returns the ``User``.
    """
    # Make sure the key we're trying conforms to the pattern of a
    # SHA1 hash; if it doesn't, no point trying to look it up in
    # the database.
    if SHA1_RE.search(activation_key):
      try:
        profile = self.get(activation_key=activation_key)
      except self.model.DoesNotExist:
        return False
      if not profile.activation_key_expired():
        user = profile.user
        user.is_active = True
	user.attrs['login'] = 0
	user.save()
        return user
    return False
    
  def create_inactive_user(self, username, password, email,
	send_email=True, profile_callback=None):
    """
    Creates a new, inactive ``User``, generates a
    ``RegistrationProfile`` and emails its activation key to the
    ``User``. Returns the new ``User``.
    To disable the email, call with ``send_email=False``.
    To enable creation of a custom user profile along with the
    ``User`` (e.g., the model specified in the
    ``AUTH_PROFILE_MODULE`` setting), define a function which
    knows how to create and save an instance of that model with
    appropriate default values, and pass it as the keyword
    argument ``profile_callback``. This function should accept one
    keyword argument:
    """
    new_user = User.objects.create_user(username, email, password)
    new_user.is_active = False
    new_user.save()

    registration_profile = self.create_profile(new_user)
        
    if profile_callback is not None:
      profile_callback(user=new_user)
        
    if send_email:
      from django.core.mail import send_mail
      from django.template.loader import render_to_string

      subject = render_to_string('activation_email_subject.txt',
                                       { 'site': settings.SITE_DOMAIN })
      # Email subject *must not* contain newlines
      subject = ''.join(subject.splitlines())
            
      message = render_to_string('activation_email.txt',
	    { 'activation_key': registration_profile.activation_key,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
            'site': settings.SITE_DOMAIN })
            
      send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_user.email])
    return new_user
    
  def create_profile(self, user):
    """
    Creates a ``RegistrationProfile`` for a given
    ``User``. Returns the ``RegistrationProfile``.
    The activation key for the ``RegistrationProfile`` will be a
    SHA1 hash, generated from a combination of the ``User``'s
    username and a random salt.
    """
    salt = sha.new(str(random.random())).hexdigest()[:5]
    activation_key = sha.new(salt+user.username).hexdigest()
    return self.create(user=user,
	    activation_key=activation_key)
        
  def delete_expired_users(self):
    """
    Removes expired instances of ``RegistrationProfile`` and their
    associated ``User``s.
    Accounts to be deleted are identified by searching for
    instances of ``RegistrationProfile`` with expired activation
    keys, and then checking to see if their associated ``User``
    instances have the field ``is_active`` set to ``False``; any
    ``User`` who is both inactive and has an expired activation
    key will be deleted.
    """
    for profile in self.all():
      if profile.activation_key_expired():
        user = profile.user
        if not user.is_active:
          user.delete()

class RegistrationProfile(models.Model):
  """
  This model's sole purpose is to store data temporarily during
  account registration and activation, and a mechanism for
  automatically creating an instance of a site-specific profile
  model is provided via the ``create_inactive_user`` on
  ``RegistrationManager``.
  """
  user = models.ForeignKey(User, unique=True)
  activation_key = models.CharField(max_length=40)

  objects = RegistrationManager()
    
  class Meta:
    verbose_name = _('registration profile')
    verbose_name_plural = _('registration profiles')
    
  class Admin:
    list_display = ('__str__', 'activation_key_expired')
    search_fields = ('user__username', 'user__first_name')
        
  def __unicode__(self):
    return u"Registration information for %s" % self.user
    
  def activation_key_expired(self):
    """
    Determines whether this ``RegistrationProfile``'s activation
    key has expired.
    Returns ``True`` if the key has expired, ``False`` otherwise.
        
    Key expiration is determined by the setting
    ``ACCOUNT_ACTIVATION_DAYS``, which should be the number of
    days a key should remain valid after an account is registered.
    """
    expiration_date = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
    return self.user.date_joined + expiration_date <= datetime.datetime.now()
  activation_key_expired.boolean = True

class ChPw(models.Model):
  """
  This model stores data during password changing.
  """
  user = models.ForeignKey(User, unique=True)
  key = models.CharField(max_length=40)

  class Admin:
    pass

  class Meta:
    verbose_name = _('Requests for changing password')

  def create_temporary_record(self, user, email_template_name='chpw_email.txt'):
    """
    creates temporary record and sends key, required for password changing 
    to user
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.core.mail import send_mail
    salt = sha.new(str(random.random())).hexdigest()[:5]
    key = sha.new(salt+user.username).hexdigest()
    subject = render_to_string('chpw_email_subject.txt',
	{ 'site': settings.SITE_DOMAIN })
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    message = render_to_string(email_template_name,
	    { 'key': key,
            'expiration_days': datetime.timedelta(settings.PWD_CHANGE_EXPIRATION_DAYS),
            'site': settings.SITE_DOMAIN })
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    self.user = user
    self.key = key
    self.save()
  
  def key_expired(self):
    expiration_date = datetime.timedelta(days=settings.PWD_CHANGE_EXPIRATION_DAYS)
    return self.user.date_joined + expiration_date <= datetime.datetime.now()
  key_expired.boolean = True

class PersonalMessage(models.Model):
    rply = models.ForeignKey(User, related_name='rply')
    rcpt = models.ManyToManyField(User, related_name="private_recipients")
    subj = models.CharField(max_length=254, db_index=True)
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    body = models.TextField(_('message'), db_index=True)
    ip = models.IPAddressField(blank=True)

    def save(self, request):
	self.ip = request.META.get('REMOTE_ADDR', None)
	super(PersonalMessage, self).save()

    def __unicode__(self):
	return self.subj

pre_save.connect(_user_pre_save, sender=User)
post_init.connect(_add_attrs_and_methods, sender=User)

