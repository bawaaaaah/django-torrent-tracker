import logging
import datetime

from django import forms
from django.conf import settings
from django.contrib.auth import decorators
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import connection
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.core.paginator import QuerySetPaginator, Paginator
from django.views.decorators.http import require_http_methods

from utils import get_page

try:
    from notification import models as notification
except ImportError:
    notification = None

from board.forms import *
from board.models import *
from board.rpc import *

from users.models import User
from users.forms import LoginForm, AuthForm

_log = logging.getLogger('board.views')

DEFAULT_USER_SETTINGS  = UserSettings()

RPC_OBJECT_MAP = {
        "thread": Thread,
        "post": Post,
        }

RPC_ACTION_MAP = {
        "censor": rpc_censor,
        "gsticky": rpc_gsticky,
        "csticky": rpc_csticky,
        "close": rpc_close,
        "abuse": rpc_abuse,
        "watch": rpc_watch,
        "quote": rpc_quote,
        }

def get_user_settings(user):
    if not user.is_authenticated():
        return DEFAULT_USER_SETTINGS
    try:
        return user.sb_usersettings
    except UserSettings.DoesNotExist:
        return DEFAULT_USER_SETTINGS

def login_context(request):
    """
    All content pages that have additional content for authenticated users but
    that are also publicly viewable should have a login form in the side panel.
    """
    response_dict = {}
    if not request.user.is_authenticated():
        response_dict.update({
                'login_form': LoginForm(),
                'openid_form': AuthForm(request.session, request.POST),
                })

    return response_dict
extra_processors = [login_context]


def rpc(request):
    """
    Delegates simple rpc requests.
    """
    if not request.POST or not request.user.is_authenticated():
        return HttpResponseServerError()

    response_dict = {}

    try:
        action = request.POST['action'].lower()
        rpc_func = RPC_ACTION_MAP[action]
    except KeyError:
        raise HttpResponseServerError()

    if action == 'quote':
        try:
            return HttpResponse(simplejson.dumps(rpc_func(request, oid=int(request.POST['oid']))))
        except (KeyError, ValueError):
            return HttpResponseServerError()

    try:
        # oclass_str will be used as a keyword in a function call, so it must
        # be a string, not a unicode object (changed since Django went
        # unicode). Thanks to Peter Sheats for catching this.
        oclass_str =  str(request.POST['oclass'].lower())
        oclass = RPC_OBJECT_MAP[oclass_str]
    except KeyError:
        return HttpResponseServerError()

    try:
        oid = int(request.POST['oid'])

        forum_object = oclass.objects.get(pk=oid)

        response_dict.update(rpc_func(request, **{oclass_str:forum_object}))
        return HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')

    except oclass.DoesNotExist:
        return HttpResponseServerError()
    except KeyError:
        return HttpResponseServerError()

def thread(request, thread_id):
    try:
        thr = Thread.view_manager.get(pk=thread_id)
    except Thread.DoesNotExist:
        raise Http404

    if not thr.category.can_read(request.user):
        raise PermissionError

    render_dict = {}

    if request.user.is_authenticated():
        render_dict.update({"watched": WatchList.objects.filter(user=request.user, thread=thr).count() != 0})

    if request.POST:
        if not thr.category.can_post(request.user):
            raise PermissionError
        postform = PostForm(request.POST)
        if postform.is_valid():
            postobj = Post(thread = thr,
                    user = request.user,
                    text = postform.cleaned_data['post'],
                    )
            postobj.save() # this needs to happen before many-to-many private is assigned

            if len(postform.cleaned_data['private']) > 0:
                _log.debug('thread(): new post private = %s' % postform.cleaned_data['private'])
                postobj.private = postform.cleaned_data['private']
                postobj.is_private = True
                postobj.save()
            postobj.notify()
            return HttpResponseRedirect(reverse('board_locate_post',
                args=(postobj.id,)))
    else:
        postform = PostForm()

    # this must come after the post so new messages show up
    post_list = Post.view_manager.posts_for_thread(thread_id, request.user)
    user_settings = get_user_settings(request.user)
    if user_settings.reverse_posts:
        post_list = post_list.order_by('-odate')
    post_list = QuerySetPaginator(post_list, user_settings.ppp)

    render_dict.update({
            'result': get_page(request.GET.get('page', 1), post_list),
            'thr': thr,
            'postform': postform,
            'category': thr.category,
            })
    
    return render_to_response('board/thread.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))

def edit_post(request, original, next=None):
    """
    Edit an existing post.decorators in python
    """
    if not request.method == 'POST':
        raise Http404

    try:
        orig_post = Post.view_manager.get(pk=int(original))
    except Post.DoesNotExist:
        raise Http404
        
    if (orig_post.user != request.user and not request.user.is_staff and not request.user.is_superuser) or not orig_post.thread.category.can_post(request.user):
        raise PermissionError

    postform = PostForm(request.POST)
    if postform.is_valid():
        # create the post
        post = Post(
                user = orig_post.user,
                thread = orig_post.thread,
                text = postform.cleaned_data['post'],
                previous = orig_post,
                )
        post.attrs['editor'] = request.user
        post.save()
        post.private = orig_post.private.all()
        post.is_private = orig_post.is_private
        post.save()

        orig_post.revision = post
        orig_post.save()

        div_id_num = post.id
    else:
        div_id_num = orig_post.id

    try:
        next = request.POST['next'].split('#')[0] + '#snap_post' + str(div_id_num)
    except KeyError:
        next = reverse('board_locate_post', args=(orig_post.id,))

    return HttpResponseRedirect(next)

##
# Should new discussions be allowed to be private?  Leaning toward no.
def new_thread(request, cat_id):
    """
    Start a new discussion.
    """
    category = get_object_or_404(Category, pk=cat_id)
    if not category.can_create_thread(request.user):
        raise PermissionError

    if request.POST:
        threadform = ThreadForm(request.POST)
        if threadform.is_valid():
            # create the thread
            thread = Thread(
                    subject = threadform.cleaned_data['subject'],
                    category = category,
                    )
            thread.save()

            # create the post
            post = Post(
                    user = request.user,
                    thread = thread,
                    text = threadform.cleaned_data['post'],
                    )
            post.save()

            # redirect to new thread
            return HttpResponseRedirect(reverse('board_thread',
                args=(thread.id,)))
    else:
        threadform = ThreadForm()

    return render_to_response('board/newthread.html',
            {
            'form': threadform,
            'category': category,
            },
            context_instance=RequestContext(request, processors=extra_processors))
new_thread = login_required(new_thread)


def favorite_index(request):
    """
    This page shows the threads/discussions that have been marked as 'watched'
    by the user.
    """
    thread_list = filter(lambda t: t.category.can_view(request.user), Thread.view_manager.get_favorites(request.user))

    render_dict = {'title': _("Watched Discussions"), 'threads': thread_list}

    return render_to_response('board/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))
favorite_index = login_required(favorite_index)

def private_index(request):
    thread_list = [thr for thr in Thread.view_manager.get_private(request.user) if thr.category.can_read(request.user)]

    render_dict = {'title': _("Discussions with private messages to you"), 'threads': thread_list}

    return render_to_response('board/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))
private_index = login_required(private_index)

def category_thread_index(request, cat_id):
    try:
        cat = Category.objects.get(pk=cat_id)
        if not cat.can_read(request.user):
            raise PermissionError
        user_settings = get_user_settings(request.user)
        thread_list = QuerySetPaginator(
            Thread.view_manager.get_category(cat_id),
            user_settings.tpp
        )
        render_dict = ({'title': ''.join((_("Category: "), cat.label)),
            'category': cat, 
            'result': get_page(request.GET.get('page', 1), thread_list),
            'ppp': user_settings.tpp,
        })
    except Category.DoesNotExist:
        raise Http404
    return render_to_response('board/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))

def thread_index(request):
    if request.user.is_authenticated():
        # filter on user prefs
        thread_list = Thread.view_manager.get_user_query_set(request.user)
    else:
        thread_list = Thread.view_manager.get_query_set()
    user_settings = get_user_settings(request.user)
    thread_list = QuerySetPaginator(
        filter(lambda t: t.category.can_view(request.user), thread_list),
        user_settings.tpp
    )
    render_dict = {
	'title': _("Recent Discussions"),
	'result': get_page(request.GET.get('page', 1), thread_list),
        'ppp': user_settings.tpp,
    }
    return render_to_response('board/thread_index.html', render_dict,
        context_instance=RequestContext(request, processors=extra_processors))

def locate_post(request, post_id):
    """
    Redirects to a post, given its ID.
    """
    post = get_object_or_404(Post, pk=post_id)
    if not post.thread.category.can_read(request.user):
        raise PermissionError
    if post.is_private and not (post.user==request.user or post.private.filter(pk=request.user.id).count()):
        raise PermissionError
    # Count the number of visible posts before the one we are looking for, 
    # as well as the total
    total = post.thread.count_posts(request.user)
    preceding_count = post.thread.count_posts(request.user, before=post.date)
    # Check the user's settings to locate the post in the various pages
    settings = get_user_settings(request.user)
    ppp = settings.ppp
    if total < ppp:
        page = 1
    elif settings.reverse_posts:
        page = (total - preceding_count - 1) // ppp + 1
    else:
        page = preceding_count // ppp + 1
    return HttpResponseRedirect('%s?page=%i#snap_post%i' % (
        reverse('board_thread', args=(post.thread.id,)), page, post.id))

def category_index(request):
    return render_to_response('board/category_index.html',
            {
            'cat_list': [c for c in Category.objects.all() if c.can_view(request.user)],
            },
            context_instance=RequestContext(request, processors=extra_processors))

def edit_settings(request):
    """
    Allow user to edit his/her profile. Requires login.
    """
    try:
        userdata = UserSettings.objects.get(user=request.user)
    except UserSettings.DoesNotExist:
        userdata = UserSettings.objects.create(user=request.user)
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=userdata, user=request.user)
        if form.is_valid():
            form.save(commit=True)
    else:
        form = UserSettingsForm(instance=userdata, user=request.user)
    return render_to_response(
            'board/edit_settings.html',
            {'form': form},
            context_instance=RequestContext(request, processors=extra_processors))
edit_settings = login_required(edit_settings)

def manage_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if not group.has_admin(request.user):
        raise PermissionError
    render_dict = {'group': group, 'invitation_form': InviteForm()}
    if request.GET.get('manage_users', False):
        render_dict['users'] = group.users.all()
    elif request.GET.get('manage_admins', False):
        render_dict['admins'] = group.admins.all()
    elif request.GET.get('pending_invitations', False):
        render_dict['pending_invitations'] = group.sb_invitation_set.filter(accepted=None)
    elif request.GET.get('answered_invitations', False):
        render_dict['answered_invitations'] = group.sb_invitation_set.exclude(accepted=None)
    return render_to_response(
            'board/manage_group.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))
manage_group = login_required(manage_group)

def invite_user_to_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if not group.has_admin(request.user):
        raise PermissionError
    if request.method == 'POST':
        form = InviteForm(request.POST)
        if form.is_valid():
            invitee = form.cleaned_data['user']
            if group.has_user(invitee):
                invitation = None
                request.user.message_set.create(message=_('The user %s is already a member of this group.') % invitee)
            else:
                invitation = Invitation.objects.create(
                        group=group,
                        sent_by=request.user,
                        sent_to=invitee)
                request.user.message_set.create(message=_('A invitation to join this group was sent to %s.') % invitee)
            return render_to_response('board/invite_user.html',
                    {'invitation': invitation, 'form': InviteForm(), 'group': group},
                    context_instance=RequestContext(request, processors=extra_processors))
    else:
        form = InviteForm()
    return render_to_response('board/invite_user.html',
            {'form': form, 'group': group},
            context_instance=RequestContext(request, processors=extra_processors))
invite_user_to_group = login_required(invite_user_to_group)

def remove_user_from_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if not group.has_admin(request.user):
        raise PermissionError
    if request.method == 'POST':
        done = False
        user = User.objects.get(pk=int(request.POST.get('user_id', 0)))
        only_admin = int(request.POST.get('only_admin', 0))
        if not only_admin and group.has_user(user):
            group.users.remove(user)
            done = True
        if group.has_admin(user):
            group.admins.remove(user)
            if notification:
                notification.send(
                    [user],
                    'group_admin_rights_removed',
                    {'group': group})
            done = True
        if done:
            if only_admin:
                request.user.message_set.create(message=_('The admin rights of user %s were removed for the group.') % user)
            else:
                request.user.message_set.create(message=_('User %s was removed from the group.') % user)
        else:
            request.user.message_set.create(message=_('There was nothing to do for user %s.') % user)
    else:
        raise Http404
    return HttpResponse('ok')
remove_user_from_group = login_required(remove_user_from_group)

def grant_group_admin_rights(request, group_id):
    """
    Although the Group model allows non-members to be admins, this view won't 
    let it.
    """
    group = get_object_or_404(Group, pk=group_id)
    if not group.has_admin(request.user):
        raise PermissionError
    if request.method == 'POST':
        user = User.objects.get(pk=int(request.POST.get('user_id', 0)))
        if not group.has_user(user):
            request.user.message_set.create(message=_('The user %s is not a group member.') % user)
        elif group.has_admin(user):
            request.user.message_set.create(message=_('The user %s is already a group admin.') % user)
        else:
            group.admins.add(user)
            request.user.message_set.create(message=_('The user %s is now a group admin.') % user)
            if notification:
                notification.send(
                    [user],
                    'group_admin_rights_granted',
                    {'group': group})
                notification.send(
                    list(group.admins.all()),
                    'new_group_admin',
                    {'new_admin': user, 'group': group})
    else:
        raise Http404
    return HttpResponse('ok')
grant_group_admin_rights = login_required(grant_group_admin_rights)

def discard_invitation(request, invitation_id):
    if not request.method == 'POST':
        raise Http404
    invitation = get_object_or_404(Invitation, pk=invitation_id)
    if not invitation.group.has_admin(request.user):
        raise PermissionError
    was_pending = invitation.accepted is not None
    invitation.delete()
    if was_pending:
        request.user.message_set.create(message=_('The invitation was cancelled.'))
    else:
        request.user.message_set.create(message=_('The invitation was discarded.'))
    return HttpResponse('ok')
discard_invitation = login_required(discard_invitation)

def answer_invitation(request, invitation_id):
    invitation = get_object_or_404(Invitation, pk=invitation_id)
    if request.user != invitation.sent_to:
        raise Http404
    form = None
    if request.method == 'POST':
        if invitation.accepted is not None:
            return HttpResponseRedirect('')
        form = AnwserInvitationForm(request.POST)
        if form.is_valid():
            if int(form.cleaned_data['decision']):
                invitation.group.users.add(request.user)
                invitation.accepted = True
                request.user.message_set.create(message=_('You are now a member of the group %s.') % invitation.group.name)
                if notification:
                    notification.send(
                        list(invitation.group.admins.all()),
                        'new_group_member',
                        {'new_member': request.user, 'group': invitation.group})
            else:
                invitation.accepted = False
                request.user.message_set.create(message=_('The invitation has been declined.'))
            invitation.response_date = datetime.datetime.now()
            invitation.save()
    elif invitation.accepted is None:
        form = AnwserInvitationForm()
    return render_to_response('board/invitation.html',
            {'form': form, 'invitation': invitation},
            context_instance=RequestContext(request, processors=extra_processors))
answer_invitation = login_required(answer_invitation)


def _brand_view(func):
    """
    Mark a view as belonging to board.

    Allows the UserBanMiddleware to limit the ban to board in larger 
    projects.
    """
    setattr(func, '_board', True)

@require_http_methods('GET')
def search(request):
    from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED, SPH_SORT_RELEVANCE
    term = request.GET.get('term', '')
    category = None
    args = [u'term=%s'%term]
    template_name = 'board/search.html'
    if term:
        sphinx = SphinxClient()
        sphinx.SetServer(settings.SPHINX_SERVER, settings.SPHINX_PORT)
        sphinx.SetMatchMode(SPH_MATCH_EXTENDED)
        sphinx.SetSortMode(SPH_SORT_RELEVANCE)
        cid = request.GET.get('c')
        if cid:
            try:
                cid = int(cid)
            except TypeError:
                raise Http404
            category = get_object_or_404(Category, cid)
            if category:
                sphinx.SetFilter('category_id', [category])
                args.append(u'c=%s'%cid)
        user_settings = get_user_settings(request.user)
        try:
            page = int(request.GET.get('page', '1'))
            if page < 1:
                raise Http404
        except ValueError:
            raise Http404
        #sphinx.SetLimits(page * user_settings.ppp, user_settings.ppp)
        if request.GET.get('adv_submit.x'):
            template_name='board/advanced_search.html'
            u = User.objects.filter(username=term)
            if u:
                q = QuerySetPaginator(Post.objects.filter(user=u),
                    user_settings.ppp)
            else:
                q = Paginator([], 1).page(1)
        else:
            result = sphinx.Query(u'@@relaxed %s'%term)
            if not result.has_key('total_found'):
                template_name = 'board/search_unavailable.html'
            pages = result.get('total_found', 0) / user_settings.ppp
            if pages > 0 and page > pages:
                raise Http404
            ids = [m['id'] for m in result.get('matches', [])]
            q = QuerySetPaginator(Post.view_manager.filter(id__in=ids),
                user_settings.ppp)
            q = get_page(request.GET.get('page', 1), q)
    else:
        q = Paginator([], 1).page(1)
    return render_to_response(template_name, {
        'result': q,
        'term': term,
        'category': category,
        'args': u'&'.join(['']+args),
    }, context_instance=RequestContext(request, processors=extra_processors))


def del_thread(request, the_id):
    if not request.user.is_staff:
        raise HttpResponseForbidden("You have no permission to delete threads")
    thread = Thread.objects.filter(id=the_id)
    if thread:
        thread[0].delete()
    return HttpResponseRedirect('/forum/')


_brand_view(search)
_brand_view(rpc)
_brand_view(thread)
_brand_view(edit_post)
_brand_view(new_thread)
_brand_view(favorite_index)
_brand_view(private_index)
_brand_view(category_thread_index)
_brand_view(thread_index)
_brand_view(locate_post)
_brand_view(category_index)
_brand_view(edit_settings)
_brand_view(manage_group)
_brand_view(invite_user_to_group)
_brand_view(remove_user_from_group)
_brand_view(grant_group_admin_rights)
_brand_view(discard_invitation)
_brand_view(answer_invitation)

# vim: ai ts=4 sts=4 et sw=4
