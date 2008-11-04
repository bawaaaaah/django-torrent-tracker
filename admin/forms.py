from django import forms
from board.models import Thread, Forum
from fs.forms import TopicEditForm
from fs.models import SECTIONS

class AdminTopicEditForm(TopicEditForm):
    screenshots = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'style':'width: 30em;'}), required=False)
    section = forms.ChoiceField(required=True, choices=SECTIONS , widget=forms.RadioSelect)

    def save(self):
	from settings import MEDIA_ROOT
	import os
	if self.instance.attrs.has_key('scrs'):
	    if self.cleaned_data['screenshots']:
		l = self.instance.attrs['scrs']
		for s in self.cleaned_data['screenshots'].split():
		    if s in l:
			l.remove(s)
			try:
			    os.unlink(os.path.join(MEDIA_ROOT, 'scr', s))
			    os.unlink(os.path.join(MEDIA_ROOT, 'iscr', s))
			except OSError:
			    pass
		self.instance.attrs['scrs'] = l
	super(AdminTopicEditForm, self).save()

class ThreadEditForm(forms.ModelForm):
    class Meta:
	model = Thread
	exclude = ('closed', 'csticky', 'gsticky', 'slug')

    def __init__( self, *args, **kwargs ):
	super( ThreadForm, self ).__init__( *args, **kwargs )
	self.fields['forums'] = forms.ChoiceField(
	    choices = [(str(x.id), x.name) for x in Forum.objects.all()]
	)
    subject = forms.CharField(max_length=160, widget=forms.TextInput)
    text = forms.CharField(widget=forms.Textarea)
    def clean_forums(self):
	return int(self.cleaned_data['forums'])
    def save(self):
	self.instance.subject = self.cleaned_data['subject']
	self.insatnce.forum = self.cleaned_data['forums']
	self.instance.text = self.cleaned_data['text']
	self.instance.save()

