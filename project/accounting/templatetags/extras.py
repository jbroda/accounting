from django import template
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import datetime
import uuid

register = template.Library()

@register.filter(name='addcss')
def addcss(field, css):
    attrs = {}
    definition = css.split(',')

    for d in definition:
        if ':' not in d:
            c = attrs.get('class')
            if c:
                attrs['class'] = c + " " + d
            else:
                attrs['class'] = d
        else:
            t, v = d.split(':')
            attrs[t] = v

    return field.as_widget(attrs=attrs)

@register.filter
def classname(obj):
    classname = obj.__class__.__name__
    return classname

@register.filter
def get_at_index(list, index):
    return list.get(index)

@register.simple_tag
def next_month():
    now = timezone.make_aware(datetime.datetime.now(), 
                              timezone.get_default_timezone())
    next_month = now + relativedelta(months=1)
    return next_month.strftime('%B')

@register.simple_tag
def uuid4():
    return uuid.uuid4()
