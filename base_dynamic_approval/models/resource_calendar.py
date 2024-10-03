# -*- coding: utf-8 -*-
from datetime import datetime

import pytz
from odoo import models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    def _time_within(self, target_dt, tz=None):
        """ Return true if datetime intersection.
        """
        self.ensure_one()
        _tz = pytz.timezone(self.tz)
        _today = str(datetime.today().weekday())
        for interval in self.attendance_ids.filtered(lambda day: day.dayofweek == _today):
            hour_begin = int(interval.hour_from)
            hour_end = int(interval.hour_to)
            minute_begin = int((interval.hour_from * 60) % 60)
            minute_end = int((interval.hour_to * 60) % 60)
            start = datetime.now(tz=_tz).replace(hour=hour_begin, minute=minute_begin)
            end = datetime.now(tz=_tz).replace(hour=hour_end, minute=minute_end)
            if start <= target_dt <= end:
                return True
        return False
