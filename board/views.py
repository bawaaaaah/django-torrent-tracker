from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.shortcuts import render_to_response, get_object_or_404
from django.core.paginator import QuerySetPaginator, Paginator
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from board.models import Forum, Thread, Post, AbuseReport
from board.forms import ThreadForm, PostForm
from users.views import login_required
from utils import HttpResponseRedirect, get_page
from settings import BBS_RESULTS_ON_PAGE, BBS_ORPHANS

@require_http_methods('GET')
def thread_index(request, forum_slug=''):
    render_dict = {'user': request.user}
    if forum_slug == 'watched':
	thread_list = Thread.view_manager.get_watched(request.user)
	render_dict.update({'title': _("Watched Discussions")})
    elif not forum_slug:
	render_dict.update({'title': _("Recent Discussions")})
	thread_list = Thread.view_manager.get_query_set()
    else:
	f = get_object_or_404(Forum, slug=forum_slug)
	render_dict.update({'title': u"%s: '%s'"%(_("Forum"), f.name)})
	thread_list = Thread.view_manager.get_forum(forum_slug)

    q = QuerySetPaginator(thread_list, BBS_RESULTS_ON_PAGE, orphans=BBS_ORPHANS)
    q = get_page(request.GET.get('page', 0), q)
    render_dict.update({'result': q})
    return render_to_response('board/thread_index.html', render_dict)

@login_required
def new_thread(request):
    if request.method == 'POST':
	form = ThreadForm(request.POST, request.FILES)
	if form.is_valid():
	    slug = form.save(request)
	    return HttpResponseRedirect("/bbs/topics/%s/"%slug)
    else:
	form = ThreadForm()
    return render_to_response('board/newthread.html', {
	'form': form,
    }, context_instance=RequestContext(request))

def thread(request, slug='', page=0):
    thread = get_object_or_404(Thread, slug=slug)
    render_dict = {'watched': False, 'thread': thread, 'user': request.user}
    if request.user.is_authenticated():
	if thread.id in request.user.attrs.get('watchlist', []):
	    render_dict.update({'watched': True})
    if request.method == "POST" and request.user.is_authenticated():
	if thread.closed:
	    return HttpResponseForbidden('Thread is closed')
	form = PostForm(request.POST, request.FILES)
	if form.is_valid():
	    form.save(request, thread)
	    return HttpResponseRedirect('/bbs/topics/%s/'%slug)
    elif request.method == "GET":
	q = get_page(request.GET.get('page', 0), QuerySetPaginator(
	    Post.view_manager.posts_for_thread(thread.id, request.user),
	    BBS_RESULTS_ON_PAGE,
	    orphans=BBS_ORPHANS,
	))
	render_dict.update({'result': q})
    form = PostForm()
    render_dict.update({'form': form})
    return render_to_response('board/thread.html', render_dict)

@login_required
@require_http_methods('GET')
def rpc(request, action, the_id):
    def _fail(r):
	r.write("<result><msg>failure</msg></result>")
	return r
    r = HttpResponse(mimetype="text/xml")
    r.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    try:
	the_id = int(the_id)
    except ValueError:
	return _fail(r)
    if action in ['close', 'censor']:
	if not request.user.is_staff:
	    return _fail(r)
	if action == 'close':
	    thread = Thread.objects.filter(pk=the_id)
	    if not thread:
		return _fail(r)
	    thread = thread[0]
	    thread.closed = not thread.closed
	    thread.save()
	else:
	    post = Post.objects.filter(pk=the_id)
	    if not post: return _fail(r)
	    post = post[0]
	    post.censored = not post.censored
	    post.save(request)
	r.write("<result><msg>success</msg></result>")
	return r
    if action == 'watch':
	if request.user.attrs.has_key('watchlist'):
	    l = request.user.attrs['watchlist']
	    if the_id not in l:
		l.append(the_id)
	    else:
		l.remove(the_id)
	    request.user.attrs['watchlist'] = l
	else:
	    request.user.attrs['watchlist'] = [the_id]
	request.user.save()
	r.write("<result><msg>success</msg></result>")
	return r
    elif action == 'abuse':
	post = Post.objects.filter(pk=the_id)
	if not post: return _fail(r)
	post = post[0]
 	AbuseReport.objects.get_or_create(submitter=request.user, post=post)
	r.write("<result><msg>success</msg></result>")
	return r
    elif action in ['gsticky', 'csticky']:
	t = Thread.objects.filter(pk=the_id)
	if not t: return _fail(r)
	t = t[0]
	setattr(t, action, (not getattr(t, action)))
	t.save()
	r.write("<result><msg>success</msg></result>")
	return r
    return _fail(r)

@login_required
@require_http_methods('POST')
def preview(request):
    from postmarkup import render_bbcode
    r = HttpResponse()
    if not request.POST.has_key('text'):
	r.write('<span class="error">%s</span>'%_("Something gone wrong."))
	return r
    r.write(render_bbcode(request.POST['text']))
    return r

