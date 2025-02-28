from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Возвращает значение из словаря по ключу, если словарь существует"""
    if dictionary is None:
        return 0
    return dictionary.get(str(key), 0)
