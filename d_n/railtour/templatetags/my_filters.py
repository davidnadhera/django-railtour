from django.template import Library

register = Library()

@register.simple_tag
def range(a, b):
   return range(a, b)