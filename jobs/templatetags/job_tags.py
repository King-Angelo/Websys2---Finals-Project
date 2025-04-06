from django import template

register = template.Library()

@register.filter(name='has_attr')
def has_attr(user, attr):
    return hasattr(user, attr) 