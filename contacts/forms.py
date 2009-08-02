from django import forms
from django.core.mail import send_mail, BadHeaderError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from utils import HttpResponseRedirect

attrs_dict = { 'class': 'textfield' }

class ContactForm(forms.Form):
    subject = forms.CharField(label=_("Subject"), max_length=255, widget=forms.TextInput(attrs_dict))
    body = forms.CharField(label=_("Your message"), max_length=255, widget=forms.Textarea)
    email = forms.EmailField(label="e-mail", max_length=200, widget=forms.TextInput(attrs_dict))

    def save(self):
	try:
	    send_mail(self.cleaned_data['subject'], self.cleaned_data['body'], self.cleaned_data['email'], [settings.CONTACT_FORM_EMAIL], fail_silently=False)
	except BadHeaderError:
	    return HttpResponse('Invalid header found.')
	return HttpResponseRedirect('/contact/thanks/')
