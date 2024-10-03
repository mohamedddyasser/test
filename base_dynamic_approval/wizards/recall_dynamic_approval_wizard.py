# -*- coding: utf-8 -*-
from odoo import models, fields


class RecallDynamicApprovalWizard(models.TransientModel):
    _name = 'recall.dynamic.approval.wizard'
    _description = 'Recall Advanced Approval Wizard'

    name = fields.Char(
        'Reason'
    )

    def action_recall_order(self):
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')

        record = self.env[active_model].browse(active_ids)
        # if getattr(record, record._state_field) == record._state_under_approval:
        recall_reason = self.name or ''
        record._action_reset_original_state(reason=recall_reason, reset_type='recall')
