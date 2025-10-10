from django import template
register = template.Library()

@register.filter
def add_class_if_exists(bound_field, extra):
    try:
        existing = bound_field.field.widget.attrs.get('class','')
        bound_field.field.widget.attrs['class'] = (existing + ' ' + extra).strip()
    except Exception:
        pass
    return bound_field
