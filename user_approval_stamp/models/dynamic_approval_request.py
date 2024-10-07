# -*- coding: utf-8 -*-

from odoo import api, models, fields


class DynamicApprovalRequest(models.Model):
    _inherit = "dynamic.approval.request"
    _description = "Approval Request"

    approve_stamp = fields.Binary(string="Approve Stamp")
