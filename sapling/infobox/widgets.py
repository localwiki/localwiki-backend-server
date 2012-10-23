from django.forms.widgets import SplitDateTimeWidget, TimeInput, DateInput,\
    MultiWidget
from django.utils.translation import gettext_lazy as _
from utils.static import static_url
from django.utils.safestring import mark_safe


def _date_format_for_javascript(format):
    # TODO convert instead of hardcoding
    return 'yyyy-mm-dd'

def _time_format_for_javascript(format):
    return 'H:i:s'


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
        TimeInput.__init__(self, {'class': 'time'}, format = self.format)

    def render(self, name, value, attrs=None):
        input = TimeInput.render(self, name, value, attrs=attrs)
        opts = { 'timeFormat': _time_format_for_javascript(self.format) }
        script = '<script>$("#%s").timepicker(%s);</script>' % (attrs['id'],
                                                                opts)
        return input + script

    def value_from_datadict(self, data, files, name):
        time = data.get(name, None)
        if time is not None:
            time = time.upper()
        return time

    class Media:
        js = (
                static_url('jquery-timepicker/jquery.timepicker.min.js'),
        )
        css = {
            'all': (static_url('jquery-timepicker/jquery.timepicker.css'),)
        }


class DateTimeWidget(SplitDateTimeWidget):
    def __init__(self, attrs=None):
        widgets = [DateWidget, TimeWidget]
        MultiWidget.__init__(self, widgets, attrs=attrs)

    def format_output(self, rendered_widgets):
        return mark_safe(u'<div class="datetime">%s %s</div>' % \
            (rendered_widgets[0], rendered_widgets[1]))
