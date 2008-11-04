from django import template
register = template.Library()

@register.filter(name="bbcode")
def bbcode(text):
    from postmarkup import render_bbcode
    return render_bbcode(text)

