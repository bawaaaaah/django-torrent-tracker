from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.conf import settings
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response 
from django.template import RequestContext
from utils import HttpResponseRedirect
from users.util import login_without_password
from users.forms import AuthForm, PersonalForm, LoginForm, MessageForm
from users.models import User

def login_required(func):
    def wrapper(request, *args, **kwargs):
	if not request.user.is_authenticated():
	    return HttpResponseRedirect(reverse(login) + '?redirect=' + request.path)
	return func(request, *args, **kwargs)
    return wrapper

def post_redirect(request):
    return request.POST.get('redirect', request.META.get('HTTP_REFERER', '/'))

def logout(request):
    from django.contrib.auth import logout
    logout(request)
    cache.delete(str('ulc-%s' % request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)))
    return HttpResponseRedirect(post_redirect(request))

def login(request):
    if request.user.is_authenticated():
	logout(request)
    if request.method == 'POST':
	form = AuthForm(request.session, request.POST)
	if request.POST.has_key('this_is_the_login_form'):
	    return authForLoginForm(request)
	if form.is_valid():
	    if request.POST.has_key('openid_url'):
		if len(request.POST['openid_url']) > 0:
		    after_auth_redirect = form.auth_redirect(post_redirect(request), 'users.views.auth')
		    return HttpResponseRedirect(after_auth_redirect)
	redirect = post_redirect(request)
    else:
	form = AuthForm(request.session)
	redirect = request.GET.get('redirect', '/')
    return render_to_response('users/auth.html', {
	'form': form, 
	'redirect': redirect,
    }, context_instance=RequestContext(request))

def authForLoginForm(request):
    from django.contrib.auth import authenticate, login
    form = LoginForm(request.POST)
    if form.is_valid():
	user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
	if user is not None:
	    login(request, user)
	    return HttpResponseRedirect(post_redirect(request))
    return render_to_response('users/auth.html', {
	'form': form,
	'redirect': post_redirect(request),
    }, context_instance=RequestContext(request))


def auth(request):
    from django.contrib.auth import authenticate, login
    user = authenticate(session=request.session, query=request.GET)
    return_to = 'http://%s%s' % (request.get_host(), request.path)
    user = authenticate(session=request.session, query=request.GET, return_to=return_to)
    if not user:
	return HttpResponseForbidden('Authentication error')
    login(request, user)
    cache.delete(str('ulc-%s' % request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)))
    return HttpResponseRedirect(request.GET.get('redirect', '/'))

def _profile_forms(request):
    return {
	'openid': AuthForm(request.session, initial={
	    'openid_url': request.user.openid
	}),
	'personal': PersonalForm(instance=request.user),
    }

@login_required
@require_http_methods('POST')
def change_openid(request):
    forms = _profile_forms(request)
    form = forms['openid'].__class__(request.session, request.POST)
    forms['openid'] = form
    if form.is_valid():
	after_auth_redirect = form.auth_redirect(post_redirect(request), 'users.views.change_openid_complete', request.user.id)
	return HttpResponseRedirect(after_auth_redirect)
    return render_to_response('users/profile_form.html', forms, context_instance=RequestContext(request))

@login_required
@require_http_methods('POST')
def post_personal(request):
    forms = _profile_forms(request)
    form = PersonalForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
	form.save()
    forms['personal'] = form
    if request.POST.has_key('redirect'):
	return HttpResponseRedirect(request.POST['redirect'])
    return render_to_response('users/profile_form.html',
	forms, context_instance=RequestContext(request))

@login_required
def change_openid_complete(request):
    from django.contrib.auth import authenticate
    user = authenticate(session=request.session, query=request.GET)
    if not user:
	return HttpResponseForbidden('Authorization error')
    return HttpResponseRedirect(request.GET.get('redirect', '/'))

@login_required
def edit_profile(request):
    return render_to_response('users/profile_form.html', 
	_profile_forms(request),
	context_instance=RequestContext(request))

def register(request, success_url='/signup/complete/',
	profile_callback=None,
	template_name='users/registration_form.html'):
    """
    Allows a new user to register an account.
    Following successful registration, redirects to either
    ``/signup/complete/`` or, if supplied, the URL
    specified in the keyword argument ``success_url``.

    `RegistrationFormUniqueEmail`` must have a method ``save``
    which will create and return the new ``User``, and that
    method must accept the keyword argument ``profile_callback``
    
    To enable creation of a site-specific user profile object for the
    new user, pass a function which will create the profile object as
    the keyword argument ``profile_callback``. See
    ``RegistrationManager.create_inactive_user`` in the file
    ``models.py`` for details on how to write this function.
    """
    if request.user.is_authenticated():
	logout(request)
    from users.forms import RegistrationFormUniqueEmail
    from users.models import RegistrationProfile
    if request.method == 'POST':
	form = RegistrationFormUniqueEmail(request.POST)
	if form.is_valid():
	    new_user = form.save(activate=settings.ACTIVATION_ENABLED,
		profile_callback=profile_callback)
	    if settings.ACTIVATION_ENABLED:
		return HttpResponseRedirect(success_url)
	    else:
		login_without_password(request, new_user)
		return HttpResponseRedirect(success_url)
	return render_to_response(template_name, {
	    'form': form,
	}, context_instance=RequestContext(request))
    else:
	form = RegistrationFormUniqueEmail()
    return render_to_response(template_name, {
	'form': form,
    }, context_instance=RequestContext(request))

def activate(request, activation_key, template_name='users/activate.html'):
    """
    Activates a ``User``'s account, if their key is valid and hasn't expired.
    Logging in then.
    Context:
	account
	    The ``User`` object corresponding to the account, if the
	    activation was successful. ``False`` if the activation was
	    not successful.
	expiration_days
	    The number of days for which activation keys stay valid
	    after registration.
    """
    from users.models import RegistrationProfile
    activation_key = activation_key.lower()
    account = RegistrationProfile.objects.activate_user(activation_key)
    if account:
	login_without_password(request, account)
    return render_to_response(request, template_name, { 
	'account': account,
	'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
	}, context_instance=RequestContext(request))

def chpw(request, key=None, template_name='users/chpw_req.html'):
    from users.forms import PasswordChangeRequestForm, PasswordChangeForm
    if not key:
	form = PasswordChangeRequestForm(request.POST)
    else:
	form = PasswordChangeForm(key, request.POST)
    if request.method == 'POST':
	if form.is_valid():
	    if not key:
		user = form.cleaned_data['username'] or \
		    form.cleaned_data['email']
		if not user:
		    return render_to_response(template_name, {
			'form': form, 
			'error_message':
			    _(u'Please specify valid Username or E-mail.'),
		    }, context_instance=RequestContext(request))
		form.save(user)
		return HttpResponseRedirect('/chpw_urlsent/')
	    else:
		form.save(form.cleaned_data['user'], form.cleaned_data['pwd'])
		return HttpResponseRedirect('/chpw_done/')
	else:
	    return render_to_response(template_name, {
		'form': form,
	    }, context_instance=RequestContext(request))
    else:
	if not key:
	    form = PasswordChangeRequestForm()
	else:
	    form = PasswordChangeForm(key)
	return render_to_response(template_name, {
	    'form': form,
	}, context_instance=RequestContext(request))

def chpw_done(request, template_name='users/chpw_done.html'):
    return HttpResponseRedirect(post_redirect(request))

@login_required
@require_http_methods('POST')
def read_hcard(request):
    from users.models import read_hcard
    read_hcard(request.user)
    request.user.save()
    return HttpResponseRedirect('../')

@login_required
def leave_message(request, the_id=None):
    if request.method == 'GET':
	if the_id:
	    try:
		the_id = int(the_id)
	    except ValueError:
		raise Http404
	else: raise Http404
	rcpt = User.objects.filter(pk=the_id)
	if not rcpt: raise Http404
	rcpt = rcpt[0]
	form = MessageForm()
	return render_to_response("users/leave_message.html", {
	    'user': request.user,
	    'rcpt': rcpt,
	    'form': form,
	}, context_instance=RequestContext(request))
    elif request.method == 'POST':
	if request.POST.has_key('xhr'):
	    r = HttpResponse(mimetype="text/xml")
	    r.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
	    def fail():
		r.write("<result><msg>failure</msg></result>")
		return r
	else:
	    def fail():
		raise Http404
	if request.POST.has_key('rcpt'):
	    try:
		rcpt = int(request.POST['rcpt'])
	    except ValueError:
		return fail()
	
	    rcpt = User.objects.filter(pk=rcpt)
	    if not rcpt:
		return fail()
	    rcpt = rcpt[0]
	else:
	    return fail()
	form = MessageForm(request.POST)
	if form.is_valid():
	    form.save(request, rcpt)
	    if request.user.attrs.has_key('sent_messages'):
		request.user.attrs['sent_messages'] += 1
	    else:
		request.user.attrs['sent_messages'] = 1
	    request.user.save()
	    if rcpt.attrs.has_key('inbox'):
		rcpt.attrs['inbox'] += 1
	    else:
		rcpt.attrs['inbox'] = 1
	    rcpt.save()
	    if request.POST.has_key('xhr'):
		r.write("<result><msg>success</msg></result>")
		return r
	    return HttpResponseRedirect('/messages/sent/')
	if request.POST.has_key('xhr'):
	    r.write("<result><msg>failure</msg></result>")
	    return r
	return render_to_response("users/leave_message.html", {
	    'user': request.user,
	    'form': form,
	}, context_instance=RequestContext(request))
    raise Http404

@login_required
@require_http_methods('GET')
def messages(request, action, page=0):
    if action not in ['sent', 'received']: raise Http404
    from users.models import PersonalMessage
    from django.core.paginator import QuerySetPaginator, InvalidPage
    from utils import get_page
    render_dict = {}
    if action == 'sent':
	q = PersonalMessage.objects.filter(rply=request.user).order_by('-date')
	render_dict.update({'title': _("Sent messages"), 'page_id': 'sent'})
    else:
	q = PersonalMessage.objects.filter(rcpt=request.user).order_by('-date')
	render_dict.update({'title': _("Received messages"), 'page_id': 'received'})
    q = get_page(request.GET.get('page', 0),
	QuerySetPaginator(q, settings.RESULTS_ON_PAGE, orphans=settings.ORPHANS)
    )
    render_dict.update({'result': q})
    return render_to_response('users/messages.html', render_dict)
