from django import forms
from django.db import models
from django.contrib import admin
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404

from board.models import *

class PostAdmin(admin.ModelAdmin):
	model = Post
	list_display = ('user', 'date', 'thread', 'ip',)
	list_filter = ('censor', 'freespeech', 'date',)
	search_fields = ('text', 'user',)
	raw_id_fields = ('thread',)
	filter_horizontal = ('private',)

class PostInline(admin.StackedInline):
    model = Post

def abuse_report_mark_seen(modeladmin, request, queryset):
    queryset.update(seen=True)
abuse_report_mark_seen.short_description = 'mark selected reports as seen'
def abuse_report_mark_not_seen(modeladmin, request, queryset):
    queryset.update(seen=False)
abuse_report_mark_not_seen.short_description = 'mark selected reports as not seen'

class AbuseReportForm(forms.ModelForm):
    text = forms.CharField(widget=forms.widgets.Textarea)

    def __init__(self, *args, **kwargs):
        super(AbuseReportForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['text'].initial = self.instance.post.text
            self.fields['text'].help_text = """
    <a id='censor%(post_id)s' href='#snap_post%(post_id)s' onclick='set_censor("%(post_id)s");'>
     <img src='/media/img/%(show_hide)s.png' title='%(censor_uncensor)s' />
    </a> | <a href='/admin/board/post/%(post_id)s/delete/'>
     <img src='/media/img/delete.png' title='delete post'>
    </a> | 
    ban %(post_author_name)s <select class="ban_menu">
    <option value=''>-----------</option>
    <option value=30>30 min.</option>
    <option value=60>60 min.</option>
    <option value=180>5 h.</option>
    <option value=720>12 h.</option>
    <option value=1440>24 h.</option>
    <option value=10080>1 week</option>
    <option value=0>ban forever</option>
    <option value=-1>unban</option>
    </select>
    <a id="close%(thread_id)s" href="#" onclick="set_close('%(thread_id)s');">
     %(open_close)s
    </a>
    <div id='post_rpc_feedback%(post_id)s' style='width:100%%;background-color:#f33;border:1px solid #000;'></div>
    <div id='thread_rpc_feedback' style='width:100%%;background-color:#f33;'></div>

    <script language="JavaScript">
    $(document).ready(function(){
    $('.ban_menu').change(function(){
    $.getJSON("/forum/rpc/ban/", {'uid': %(post_author_id)s, 'expires': $(this).val()}, function(j){
            document.getElementById('post_rpc_feedback%(post_id)s').innerHTML = '<p class="rpc_message">%(post_author_name)s banned</p>'
        });
    });
    });
</script>
    """%{
                'post_id': self.instance.post.id,
                'show_hide': ((self.instance.post.censor and 'show') or 'hide'),
                'censor_uncensor': ((self.instance.post.censor and 'censor') or 'uncensor'),
                'post_author_name': self.instance.post.user.name,
                'post_author_id': self.instance.post.user.id,
                'thread_id': self.instance.post.thread.id,
                'open_close': ((self.instance.post.thread.closed and 'open thread') or 'close thread'),
            }

    def save_m2m(self):
        pass

    def save(self, *args, **kwargs):
        if not self.instance.pk:
            raise PermissionDenied("It is not allowed to report abuse from admin interface")
        post = Post(
            user = self.instance.post.user,
            thread = self.instance.post.thread,
            text = self.cleaned_data['text'],
            previous = self.instance.post,
        )
        post.attrs['editor'] = self.instance.submitter
        post.save()
        post.private = self.instance.post.private.all()
        post.is_private = self.instance.post.is_private
        post.save()
        self.instance.post.revision = post
        self.instance.post.save()
        self.instance.save()
        return self.instance

    class Meta:
        model = AbuseReport

class AbuseReportAdmin(admin.ModelAdmin):
        form = AbuseReportForm
        def post_text(self, o):
            return o.post.text[:200]

        def change_view(self, request, the_id):
            if not self.has_change_permission(request):
                if self.has_add_permission(request) and settings.DEBUG:
                    raise Http404("You dont have permission to change")
                raise PermissionDenied
            obj = get_object_or_404(AbuseReport, id=the_id)
            if request.method == 'POST':
                form = self.form(request.POST, instance=obj)
                if form.is_valid():
                    form.save()
                else:
                    return super(AbuseReportAdmin, self).change_view(
                        request, the_id)
            else:
                return super(AbuseReportAdmin, self).change_view(
                    request, the_id)
            return HttpResponseRedirect('/admin/board/abusereport/')

        def add_view(self, request):
            if not self.has_change_permission(request):
                if self.has_add_permission(request) and settings.DEBUG:
                    raise Http404("You dont have permission to add")
                raise PermissionDenied
            if request.method == 'POST':
                form = self.form(request.POST, instance=AbuseReport(
                    submitter = request.user))
                if form.is_valid():
                    form.save()
            else:
                return super(AbuseReportAdmin, self).add_view(request)
            return HttpResponseRedirect('/admin/board/abusereport/')

        def redirect_to_post(self, *a, **kw):
            if not self.instance.pk:
                return HttpResponseRedirect('/admin/board/abusereport/')
            return HttpResponseRedirect('/forum/threads/id/%s/#snap_post%s'%(
                self.instance.post.thread.id, self.instance.post.id))

        def get_urls(self):
            from django.conf.urls.defaults import patterns
            #if not self.instance.pk:
            #    return None
            return patterns('',
                (r'^(\d+)/post/$',
                    self.admin_site.admin_view(self.redirect_to_post))
            ) + super(AbuseReportAdmin, self).get_urls()

	list_display = ('post_text', 'submitter', 'seen')
        fieldsets = (
            (None, {
                'fields': ('submitter', 'seen', 'text')
            }),
        )
        actions = [abuse_report_mark_seen, abuse_report_mark_not_seen]
        search_fields = ['submitter', 'seen', 'post_text']

class ThreadAdmin(admin.ModelAdmin):
	model = Thread
	list_display = ('subject', 'category',)
	list_filter = ('closed', 'csticky', 'gsticky', 'category',)

class UserBanAdmin(admin.ModelAdmin):
	model = UserBan
	list_display = ('user', 'reason', 'expires',)
	search_fields = ('user', 'reason', 'expires',)
	raw_id_fields = ('user',)

class IPBanAdmin(admin.ModelAdmin):
	model = IPBan
	list_display = ('address', 'reason',)
	search_fields = ('address', 'reason',)

class GroupAdmin(admin.ModelAdmin):
    model = Group
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('users', 'admins',)

admin.site.register(Category)
admin.site.register(Moderator)
admin.site.register(Post, PostAdmin)
admin.site.register(AbuseReport, AbuseReportAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(UserSettings)
admin.site.register(UserBan, UserBanAdmin)
admin.site.register(IPBan, IPBanAdmin)
admin.site.register(Group, GroupAdmin)

# vim: ai ts=4 sts=4 et sw=4

