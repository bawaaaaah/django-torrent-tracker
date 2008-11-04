from django import template
import captcha
from settings import RECAPTCHA_PUB_KEY
register = template.Library()
 
def recaptcha(context):
        return {'captcha': captcha.displayhtml(RECAPTCHA_PUB_KEY)}
 
register.inclusion_tag("captcha.html", takes_context=True)(recaptcha)
