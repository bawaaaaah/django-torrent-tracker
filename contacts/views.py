from django.shortcuts import render_to_response
from contacts.forms import *

def contact(request):
    if request.method == 'POST':
	form = ContactForm(request.POST)
	if form.is_valid():
	    return form.save()
	return render_to_response('contacts/form.html', {
	    'form': form,
	}, context_instance=RequestContext(request))
    form = ContactForm()
    return render_to_response('contacts/form.html', {
	'form': form,
    })
