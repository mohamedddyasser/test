# -*- coding: utf-8 -*-

from datetime import datetime
import logging
from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DynamicApprovalMixin(models.AbstractModel):
    _inherit = "dynamic.approval.mixin"

    def _prepare_request_vals(self, note="", signature=False, stamp=False):
        vals = super(DynamicApprovalMixin, self)._prepare_request_vals(
            note=note, signature=signature, stamp=stamp
        )
        if self.env.user.has_group(
            "user_approval_stamp.group_allow_approval_with_stamp"
        ):
            vals.update({"approve_stamp": stamp})
        return vals
