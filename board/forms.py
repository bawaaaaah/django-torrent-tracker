from django import forms
from sets import Set
from board.models import Forum, Thread, Post
from django.utils.translation import ugettext_lazy as _
from utils import validate_image, save_imgs
from django.contrib.auth.models import User
from users.models import PersonalMessage

class PostForm(forms.ModelForm):
    class Meta:
	model = Post
	fields = ('text', 'private', 'image')

    text = forms.CharField(widget=forms.Textarea)
    private = forms.CharField(label=_("Recipients"), max_length=150, required=False)
    image = forms.ImageField(required=False)

    def clean_image(self):
	return validate_image(self.cleaned_data['image'])

    def clean_private(self):
	recipients = self.cleaned_data['private']
	if len(recipients.strip()) < 1:
	    return []
	recipients = filter(lambda x: len(x.strip()) > 0, recipients.split(','))
	recipients = Set([x.strip() for x in recipients]) # string of usernames
	u = User.objects.filter(username__in=recipients).order_by('username')
	if len(u) != len(recipients):
	    u_set = Set([str(x.username) for x in u])
	    u_diff = recipients.difference(u_set)
	    raise forms.ValidationError("The following are not valid user(s): " + ' '.join(u_diff))
	return u

    def clean_text(self):
	text = self.cleaned_data['text'].strip()
	if len(text) == 0:
	    raise forms.ValidationError("This field is required.")
	return text

    def save(self, request, thread):
	if self.cleaned_data['private']:
	    msg = PersonalMessage()
	    msg.rply = request.user
	    msg.subj = thread.subject
	    msg.body = self.cleaned_data['text']
	    msg.save(request)
	    msg.rcpt = self.cleaned_data['private']
	    msg.save(request)
	    if request.user.attrs.has_key('sent_messages'):
		request.user.attrs['sent_messages'] +=1
	    else:
		request.user.attrs['sent_messages'] = 1
	    request.user.save()
	    for u in self.cleaned_data['private']:
		if u.attrs.has_key('inbox'):
		    u.attrs['inbox'] += 1
		else:
		    u.attrs['inbox'] = 1
		u.save()
	else:
	    post = Post()
	    post.author = request.user
	    post.thread = thread
	    post.text = self.cleaned_data['text']
	    if self.cleaned_data['image']:
		post.image = save_imgs(self.cleaned_data['image'], request.user.id, 'poster')
	    post.save(request)

class ThreadForm(forms.Form):
    def __init__(self, *args, **kwargs):
	super(ThreadForm, self).__init__(*args, **kwargs)
	self.fields['forums'] = forms.ChoiceField(
	    choices = [(str(x.id), x.name) for x in Forum.objects.all()]
	)

    subject = forms.CharField(max_length=160, widget=forms.TextInput)
    text = forms.CharField(widget=forms.Textarea)
    image = forms.ImageField(required=False)

    def clean_image(self):
	return validate_image(self.cleaned_data['image'])

    def clean_forums(self):
	return int(self.cleaned_data['forums'])

    def clean_text(self):
	text = self.cleaned_data['text'].strip()
	if len(text) == 0:
	    raise forms.ValidationError("This field is required.")
	return text

    def clean_subject(self):
	subj = self.cleaned_data['subject'].strip()
	if len(subj) == 0:
	    raise forms.ValidationError("this field is required.")
	if subj.startswith('page-') or subj.startswith('newtopic') or \
	    subj.startswith('watched') or subj.startswith('forums') or \
	    subj.startswith('topics') or subj.startswith('rpc'):
	    raise forms.ValidationError("you need to change subject")
	t = Thread.objects.filter(subject=subj)
	if t:
	    raise forms.ValidationError(_("Thread with this title already exists."))
	return subj

    def save(self, request):
	thread = Thread()
	thread.subject = self.cleaned_data['subject']
	thread.forum = Forum.objects.get(pk=self.cleaned_data['forums'])
	slug = thread.save()
	
	post = Post()
	post.author = request.user
	post.thread = thread
	post.text = self.cleaned_data['text']
	if self.cleaned_data['image']:
	    post.image = save_imgs(self.cleaned_data['image'], request.user.id, 'poster')
	post.save(request)
	return slug
