from users.views import login_required
from django.core.paginator import QuerySetPaginator, InvalidPage
from django.http import Http404, HttpResponseForbidden, HttpResponse
from fs.models import Topic
from board.models import Post, Thread
from django.shortcuts import render_to_response, get_object_or_404
from utils import HttpResponseRedirect

@login_required
def delete(request, name='', the_id=None):
    if not request.user.is_superuser:
	HttpResponseForbidden("Go away.")
    if not the_id: raise Http404('Not found')
    if name == 'topics':
	vic = get_object_or_404(Topic, pk=the_id)
	title = "topic %s"%vic.title
    elif name == 'posts':
	vic = get_object_or_404(Post, pk=the_id)
	title = "post in thread %s ('%s..')"%(vic.thread.subject, text[80])
    elif name == 'threads':
	vic = get_object_or_404(Thread, pk=the_id)
	title = "thread '%s'"%vic.subject
    elif name == 'comment':
	if request.method=='GET':
	    from django.contrib.comments.models import Comment
	    comment = get_object_or_404(Comment, pk=the_id)
	    comment.delete()
	    return HttpResponseRedirect(request.GET.get('redirect', '/admin/'))
    else:
	raise Http404('Not found')
    if request.method == 'GET':
	return render_to_response('admin/confirmation.html', {
	    'name': name,
	    'the_id': the_id,
	    'title': title,
	    })
    elif request.method == 'POST':
	if not request.POST.has_key('yesno'):
	    raise Http404
	if request.POST['yesno'] == 'yes':
	    vic.delete()
    return HttpResponseRedirect('/admin/%s/'%name)

@login_required
def approve(request, the_id):
    if not request.user.is_superuser:
	HttpResponseForbidden("Go away.")
    topic = get_object_or_404(Topic, pk=the_id)
    topic.approved=True
    topic.save()
    return HttpResponseRedirect('/admin/')

@login_required
def items(request, name, page=0):
    if not request.user.is_superuser:
	HttpResponseForbidden("Go away.")
    if name == 'topics':
	lst = Topic.objects.filter(approved=False).order_by('-created')
    elif name == 'posts':
	lst = Post.objects.filter(censored=False).order_by('-created')
    elif name == 'threads':
	lst = Thread.objects.all()
    else:
	raise Http404('Not found')
    result = QuerySetPaginator(lst, 40, orphans=5)
    if result.num_pages == 0:
	raise Http404("No posts found.")
    if page:
	try:
	    r = result.page(int(page))
	except InvalidPage:
	    raise Http404
    else:
	r = result.page(1)
    return render_to_response('admin/%s.html'%name, {
	'result': r,
	'page': int(page),
	'title': '',
    })

@login_required
def edit(request, name, the_id=0):
    if not request.user.is_superuser:
	HttpResponseForbidden("Go away.")
    if name == 'topics':
	item = get_object_or_404(Topic, pk=the_id)
	#from fs.forms import TopicEditForm as Form
	from admin.forms import AdminTopicEditForm as Form
    elif name == 'posts':
	item = get_object_or_404(Post, pk=the_id)
	from board.forms import PostEditForm as Form
    elif name == 'threads':
	item = get_object_or_404(Thread, pk=the_id)
	from admin.forms import ThreadEditForm as Form
    else:
	raise Http404('Not found')
    if request.method =='POST':
	form = Form(request.POST, request.FILES, instance=item)
	if form.is_valid():
	    form.save()
    else:
	form = Form(instance=item)
    return render_to_response("admin/edit_%s.html"%name, {
	'form': form,
	'the_id': the_id,
    })

