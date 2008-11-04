from django import template

register = template.Library()

@register.filter(name="show")
def show(obj):
    f = open('/tmp/log','w')
    f.write("%s"%obj.__dict__)
    f.close()

