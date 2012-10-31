import datetime
import time

from django.forms.widgets import TimeInput, DateInput, MultiWidget
from django.utils.translation import gettext_lazy as _
from utils.static import static_url
from django.utils.safestring import mark_safe


def _date_format_for_javascript(format):
    js_format = format
    format_map = {'%Y': 'yyyy',  # year: 2014
                  '%y': 'yy',    # year: 14
                  '%m': 'mm',    # month: 09
                  '%B': 'MM',    # month: September
                  '%b': 'M',     # month: Sep
                  '%d': 'dd',    # day: 31
                 }
    for py, js in format_map.items():
        js_format = js_format.replace(py, js)
    return js_format


def _time_format_for_javascript(format):
    js_format = format
    format_map = {'%H': 'H',  # hour (24-hour)
                  '%I': 'h',  # hour (12-hour)
                  '%M': 'i',  # minutes
                  '%S': 's',  # seconds
                  '%p': 'A',  # AM/PM
                 }
    for py, js in format_map.items():
        js_format = js_format.replace(py, js)
    return js_format


class DateWidget(DateInput):
    def __init__(self):
        DateInput.__init__(self, {'class': 'date'})

    def render(self, name, value, attrs=None):
        input = DateInput.render(self, name, value, attrs=attrs)
        opts = { 'format': _date_format_for_javascript(self.format) }
        script = '<script>$("#%s").datepicker(%s);</script>' % (attrs['id'],
                                                                opts)
        return input + script

    class Media:
        js = (
              static_url('bootstrap-datepicker/js/bootstrap-datepicker.js'),
        )
        css = {
            'all': (static_url('bootstrap-datepicker/css/standalone.css'),)
        }


class TimeWidget(TimeInput):
    def __init__(self):
        TimeInput.__init__(self, {'class': 'time'})

    def render(self, name, value, attrs=None):
        input = TimeInput.render(self, name, value, attrs=attrs)
        opts = { 'timeFormat': _time_format_for_javascript(self.format) }
        script = '<script>$("#%s").timepicker(%s);</script>' % (attrs['id'],
                                                                opts)
        return input + script

    class Media:
        js = (
                static_url('jquery-timepicker/jquery.timepicker.min.js'),
        )
        css = {
            'all': (static_url('jquery-timepicker/jquery.timepicker.css'),)
        }


class DateTimeWidget(MultiWidget):
    def __init__(self, attrs=None):
        widgets = [DateWidget, TimeWidget]
        MultiWidget.__init__(self, widgets, attrs=attrs)

    def format_output(self, rendered_widgets):
        return mark_safe(u'<div class="datetime">%s %s</div>' % \
            (rendered_widgets[0], rendered_widgets[1]))

    def value_from_datadict(self, data, files, name):
        dt = MultiWidget.value_from_datadict(self, data, files, name)
        format = '%s %s' % (self.widgets[0].format, self.widgets[1].format)
        value = '%s %s' % (dt[0], dt[1])
        try:
            return datetime.datetime(*time.strptime(value, format)[:6])
        except ValueError:
            return None

    def decompress(self, value):
        if value:
            return [value.date(), value.time().replace(microsecond=0)]
        return [None, None]
