from django import forms
from django.utils.translation import ugettext_lazy as _

class FilesForm(forms.Form):
    def __init__(self, ls=None, key='', *args, **kwargs):
	super(FilesForm, self).__init__(*args, **kwargs)
	self.fields['key'] = forms.CharField(required=True, max_length=16,
	    widget=forms.HiddenInput(attrs={'value': key}))
	if not ls:
	    return
	self.ls = []
	ls = ls['dirnames']+ls['filenames']
	for i in xrange(len(ls)):
	    k = 'file_%d' % i
	    self.fields[k] = forms.BooleanField(required=False)
	    self.ls.append((k,ls[i]))

_YESNO = (
    ('yes', _('Yes')),
    ('no', _('No')),
)

class YNForm(forms.Form):
    yesno = forms.ChoiceField(required=False, choices=_YESNO, label=_('transcode ?'))

class TQForm(forms.Form):
    def __init__(self, q=None, key='', *args, **kwargs):
	super(TQForm, self).__init__(*args, **kwargs)
	self.fields['key'] = forms.CharField(required=True, max_length=16,
	    widget=forms.HiddenInput(attrs={'value': key}))
	if not q:
	    return
	self.ql = []
	for i in xrange(len(q)):
	    k = 'q_%d' % i
	    self.fields[k] = forms.CharField(required=False, max_length=10)
	    self.ql.append((k, q[i]))
	    k = 't_%d' % i
	    self.fields[k] = forms.CharField(required=False, max_length=10)

