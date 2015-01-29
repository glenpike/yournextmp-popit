from django import template

register = template.Library()
# Custom tag for diagnostics
def debug_object_dump(var):
    return vars(var)

register.simple_tag(debug_object_dump)
