from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def get_attr(obj, attr):
    """
    Template filter to get attribute from object
    Usage: {{ object|get_attr:"attribute_name" }}
    """
    try:
        return getattr(obj, attr)
    except (AttributeError, TypeError):
        try:
            return obj.get(attr)
        except (AttributeError, TypeError, KeyError):
            return ''

@register.filter
def contains(value, arg):
    """
    Template filter to check if a string contains another string
    Usage: {{ value|contains:"search_string" }}
    """
    return str(arg).lower() in str(value).lower()

@register.filter
def get_item(dictionary, key):
    """
    Sözlükten anahtar kullanarak değer almak için özel filtre
    Kullanım: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key)

@register.filter
def add_days(date, days):
    """Verilen tarihe belirtilen gün sayısını ekler"""
    return date + timedelta(days=int(days)) 


@register.filter
def add_class(field, class_name):
    """Verilen alana belirtilen sınıfı ekler"""
    return field.as_widget(attrs={'class': class_name})

@register.filter
def getattr_filter(obj, attr):
    """
    Bir nesnenin belirtilen özelliğini döndüren template filtresi.
    Kullanım: {{ object|getattr:'field_name' }}
    """
    try:
        return getattr(obj, attr)
    except (AttributeError, TypeError):
        return None

@register.filter
def filter_by_date(days, date):
    """
    Belirli bir tarihe ait operasyon günlerini filtreler
    Kullanım: {{ days|filter_by_date:date }}
    """
    return [day for day in days if day.date == date]
