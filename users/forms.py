from django import forms
from django.forms.widgets import PasswordInput
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from users.models import RegistrationProfile, ChPw, PersonalMessage
from utils import validate_image, save_imgs

class AuthForm(forms.Form):
    "The form for OpenID authentication"
    openid_url = forms.CharField(label='OpenID', max_length=200, required=True,
	widget=forms.TextInput(attrs={'class':'OpenIdLabel'}))
#    xhr = forms.CharField(required=False)

    def __init__(self, session, *args, **kwargs):
	forms.Form.__init__(self, *args, **kwargs)
	self.session = session
    
    def _site_url(self):
	return 'http://%s'%settings.SITE_DOMAIN
  
    def clean_openid_url(self):
	from users.util import get_consumer
	from openid.consumer.consumer import DiscoveryFailure
	consumer = get_consumer(self.session)
	errors = []
	try:
	    self.request = consumer.begin(self.cleaned_data['openid_url'])
	except DiscoveryFailure, e:
	    errors.append(str(e[0]))
	if hasattr(self, 'request') and self.request is None:
	    errors.append('OpenID service not found')
	if errors:
	    raise forms.ValidationError(errors)

    def auth_redirect(self, target, view_name, *args, **kwargs):
	from django.core.urlresolvers import reverse
	site_url = self._site_url()
	trust_url = settings.OPENID_TRUST_URL or (site_url + '/')
	return_to = site_url + reverse(view_name, args=args, kwargs=kwargs)
	self.request.return_to_args['redirect'] = target
	if hasattr(self, 'acquire_post'):
	    self.request.return_to_args['acquire_post'] = str(self.acquire_post.id)
	return self.request.redirectURL(trust_url, return_to)

class PersonalForm(forms.ModelForm):
    class Meta:
	model = User
	fields = ('title', 'birthday', 'im', 'image', 'email', 'text')
	exclude = ('username', 'groups', 'is_active', 'first_name', 'last_name', 'password', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'full_name', 'slug', 'openid_server', 'openid', 'prefs')

    title = forms.CharField(max_length=255, required=False, widget=forms.TextInput)
    name = forms.CharField(max_length=200, required=False, widget=forms.TextInput)
    birthday = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'vDateField'}))
    im = forms.CharField(max_length=200, required=False, widget=forms.TextInput)
    image = forms.ImageField(required=False)
    text = forms.CharField(widget=forms.Textarea, required=False)

    def clean_image(self):
	return validate_image(self.cleaned_data['image'])

    def save(self):
	if self.cleaned_data['image']:
	    self.instance.image = save_imgs(self.cleaned_data['image'], self.instance.id, 'avatar')
	if self.cleaned_data['name']:
	    self.instance.full_name = self.cleaned_data['name']
	if not self.cleaned_data['text']:
	    self.instance.text = ""
	for k in ['title', 'birthday', 'im', 'text']:
	    if self.cleaned_data[k]:
		setattr(self.instance, k, self.cleaned_data[k])
	self.instance.save()

class LoginForm(forms.Form):
    """
    login form for django.contrib.auth.backends.ModelBackend
    """
    username = forms.CharField(max_length=30, label=_('Username'))
    password = forms.CharField(widget=PasswordInput, label=_('Password'))
    def clean(self):
	user = authenticate(username=self.cleaned_data.get('username'), password=self.cleaned_data.get('password'))
	if user is None:
	    raise forms.ValidationError(_('Login or password incorrect!'))
	elif user.is_active is False:
	    if user.attrs.has_key('reason'):
		if user.attrs['reason']:
		    raise forms.ValidationError("Banned: '%s'"%user.attrs['reason'])
	    raise forms.ValidationError(_('Your account has been locked!'))
	return self.cleaned_data

class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.
    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    
    Subclasses should feel free to add any additional validation they
    need, but should either preserve the base ``save()`` or implement
    a ``save()`` which accepts the ``profile_callback`` keyword
    argument and passes it through to
    ``RegistrationProfile.objects.create_inactive_user()``.
    """
    username = forms.CharField(max_length=30, widget=forms.TextInput, label=_(u'username'))
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(maxlength=75)), label=_(u'email address'))
    password1 = forms.CharField(widget=forms.PasswordInput, label=_(u'password'))
    password2 = forms.CharField(widget=forms.PasswordInput, label=_(u'password (again)'))
    
    def clean_username(self):
	"""
	Validates that the username is alphanumeric and is not already in use.
	"""
	import re
	alnum_re = re.compile(r'^\w+$')
	if not alnum_re.search(self.cleaned_data['username']):
	    raise forms.ValidationError(_(u'Usernames can only contain letters, numbers and underscores'))
	if self.cleaned_data['username'] == 'sections':
	    raise forms.ValidationError(_(u'Invalid username'))
	try:
	    user = User.objects.get(username__exact=self.cleaned_data['username'])
	except User.DoesNotExist:
	    return self.cleaned_data['username']
	raise forms.ValidationError(_(u'This username is already taken. Please choose another.'))
    
    def clean_password2(self):
	"""
	Validates that the two password inputs match.
	"""
	if self.cleaned_data['password1'] == self.cleaned_data['password2']:
	    return self.cleaned_data['password2']
	raise ValidationError(_(u'You must type the same password each time'))
    
    def save(self, profile_callback=None, activate=None):
	"""
	Creates the new ``User`` and ``RegistrationProfile``, and
	returns the ``User``.

	This is essentially a light wrapper around
	``RegistrationProfile.objects.create_inactive_user()``,
	feeding it the form data and a profile callback (see the
	documentation on ``create_inactive_user()`` for details) if supplied.
	"""
	if not activate:
	    new_user = User.objects.create_user(
		self.cleaned_data['username'],
		email=self.cleaned_data['email'],
		password=self.cleaned_data['password2'])
	    new_user.save()
	else:
	    new_user = RegistrationProfile.objects.create_inactive_user(
	    username=self.cleaned_data['username'],
	    password=self.cleaned_data['password2'],
	    email=self.cleaned_data['email'],
	    profile_callback=profile_callback)
	return new_user

class RegistrationFormUniqueEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which enforces uniqueness of
    email addresses.
    """
    def clean_email(self):
	"""
	Validates that the supplied email address is unique for the site.
	"""
	try:
	    user = User.objects.get(email__exact=self.cleaned_data['email'])
	except User.DoesNotExist:
	    return self.cleaned_data['email']
	raise forms.ValidationError(_(u'This email address is already in use. Please supply a different email address.'))

class PasswordChangeRequestForm(forms.Form):
    "A form that lets a user to request a password reset"
    username = forms.CharField(max_length=30, widget=forms.TextInput, label=_(u'username'), required=False)
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(maxlength=75)), label=_(u'E-mail address'), required=False)

    def clean_username(self):
	"""
	Validates that valid username or email is specified.
	"""
	if len(self.cleaned_data['username']) == 0: return None
	try:
	    user = User.objects.get(username__iexact=self.cleaned_data['username'])
	except User.DoesNotExist:
	    raise forms.ValidationError(_(u"Specified  Username is invalid."))
	return user

    def clean_email(self):
	"""
	Validates that valid email or username is specified.
	"""
	if len(self.cleaned_data['email']) == 0: return None
	try:
	    user = User.objects.get(email__exact=self.cleaned_data['email'])
	except User.DoesNotExist:
	    raise forms.ValidationError(_(u"That e-mail address doesn't have an associated user account. Are you sure you've registered?"))
	return user

    def save(self, user, email_template_name='chpw_email.txt'):
	"""
	generates the key for changing password and send it to user
	"""
	ChPw.objects.filter(user=user).delete()
	ChPw().create_temporary_record(user, email_template_name)

class PasswordChangeForm(forms.Form):
    """
    Form for changing password.
    """
    def __init__(self, key=None, *args, **kwargs):
	super(PasswordChangeForm, self ).__init__(*args, **kwargs)
	self.key = key

    oldpassword = forms.CharField(widget=forms.PasswordInput, label=_(u'old password'))
    password1 = forms.CharField(widget=forms.PasswordInput, label=_(u'password'))
    password2 = forms.CharField(widget=forms.PasswordInput, label=_(u'password (again)'))

    def clean(self):
	"""
	Validates that the two password inputs match.
	"""
	try:
	    user = User.objects.get(chpw__key=self.key)
	except User.DoesNotExist:
	    raise forms.ValidationError(_(u'Invalid or expired key probably.'))

	if self.cleaned_data['password1'] != self.cleaned_data['password2']:
	    raise forms.ValidationError(_(u'You must type the same new password each time.'))

	if not user.check_password(self.cleaned_data['oldpassword']):
	    raise forms.ValidationError, _("Your old password was entered incorrectly. Please enter it again.")
	return {'user': user, 'pwd': self.cleaned_data['password2']}

    def save(self, user, pwd):
	"Saves the new password."
	user.set_password(pwd)
	user.save()
	ChPw.objects.filter(user=user).delete()

class MessageForm(forms.ModelForm):
    class Meta:
	model = PersonalMessage
	fields = ('subj', 'body')

    def save(self, request, rcpt):
	self.instance.rply = request.user
	self.instance.body = self.cleaned_data['body']
	self.instance.subj = self.cleaned_data['subj']
	self.instance.save(request)
	self.instance.rcpt.add(rcpt)
	self.instance.save(request)

    subj = forms.CharField(max_length=254, required=True, widget=forms.TextInput)
    body = forms.CharField(required=True, widget=forms.Textarea)

