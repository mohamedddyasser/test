# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError


class ApproveDynamicApprovalWizard(models.TransientModel):
    _inherit = "approve.dynamic.approval.wizard"
    _description = "Approve Advanced Approval Wizard"

    stamp_id = fields.Many2one("user.stamp", string="Stamp")
    approve_stamp = fields.Binary(string="Stamp", related="stamp_id.stamp_image")

    def action_sign_order(self):
        # if not self.approve_signature_change:
        if not self.signature:
            raise ValidationError(_("Please Insert Your Signature"))

        active_ids = self._context.get("active_ids")
        active_model = self._context.get("active_model")
        record = self.env[active_model].browse(active_ids)
        record.action_under_approval(
            note=self.note, signature=self.signature, stamp=self.approve_stamp
        )
