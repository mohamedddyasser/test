# -*- coding: utf-8 -*-
from odoo import models, fields


class DynamicApprovalRole(models.Model):
    _name = "dynamic.approval.role"
    _description = "Approval Role"
    _rec_name = "short_code"

    short_code = fields.Char(
        required=True,
    )
    name = fields.Char(
        required=True,
    )
    active = fields.Boolean(
        default=True,
    )

    def get_approval_user(self, model, res):
        """return approval user
        this function can be override to add custom users based on each model
        """
        return self.env["res.users"]
