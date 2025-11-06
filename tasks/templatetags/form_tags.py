from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    attrs = {"class": css_class}
    if not field.field.widget.attrs.get("placeholder"):
        attrs["placeholder"] = field.label
    return field.as_widget(attrs=attrs)
