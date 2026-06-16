from django import template

register = template.Library()

@register.filter
def discounted_price(product):
    return round(float(product.price) * (1 - float(product.discount) / 100), 2)

@register.filter
def get_discounted_price(price, discount):
    return round(float(price) * (1 - float(discount) / 100), 2)
