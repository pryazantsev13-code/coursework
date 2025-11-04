from django import template
from django.utils import timezone
import datetime

register = template.Library()

@register.filter
def format_time(time_obj):
    """Форматирует время в 24-часовом формате"""
    if isinstance(time_obj, (datetime.time, datetime.datetime)):
        return time_obj.strftime('%H:%M')
    return str(time_obj)

@register.filter
def format_date(date_obj):
    """Форматирует дату в русском формате"""
    if isinstance(date_obj, (datetime.date, datetime.datetime)):
        months = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        return f"{date_obj.day} {months[date_obj.month]} {date_obj.year}"
    return str(date_obj)