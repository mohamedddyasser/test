# -*- coding: utf-8 -*-
from odoo import models, fields,_
from odoo.exceptions import ValidationError, UserError

class ApproveDynamicApprovalWizard(models.TransientModel):
    _name = 'approve.dynamic.approval.wizard'
    _description = 'Approve Advanced Approval Wizard'

    note = fields.Char()
    # approve_signature_change = fields.Binary(string="Signature")
    # default_signature = fields.Binary(string="Signature", related='approve_signature_change')

    signature = fields.Binary(string='Signature')

    def action_approve_order(self):
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        record = self.env[active_model].browse(active_ids)
        record.action_under_approval(note=self.note)

    def action_sign_order(self):
        if not self.signature:
            raise ValidationError(_("Please Insert Your Signature"))
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        record = self.env[active_model].browse(active_ids)
        record.action_under_approval(note=self.note, signature=self.signature)
