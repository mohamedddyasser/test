# -*- coding: utf-8 -*-
from odoo import models, fields


class RejectDynamicApprovalWizard(models.TransientModel):
    _name = 'reject.dynamic.approval.wizard'
    _description = 'Reject Advanced Approval Wizard'

    name = fields.Char(
        'Reason'
    )

    def action_reject_order(self):
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        record = self.env[active_model].browse(active_ids)
        # if getattr(record, record._state_field) == record._state_under_approval:
        reject_reason = self.name or ''
        record._action_reset_original_state(reason=reject_reason, reset_type='reject')
