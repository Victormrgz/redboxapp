from django import template

register = template.Library()


@register.filter
def igual(valor1, valor2):
    return valor1 == valor2
