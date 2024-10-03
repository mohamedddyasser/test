# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError


class DynamicApprovalRole(models.Model):
    _inherit = 'dynamic.approval.role'

    def get_approval_user(self, model, res):
        """ return approval user
            this function can be override to add custom users based on each model
        """
        rec = super().get_approval_user(model, res)
        if model == 'sale.order' and res.vertical_analytic_account_id and \
                res.vertical_analytic_account_id.apply_approval_role:
            analytic_approval_role = res.vertical_analytic_account_id.approval_role_ids.filtered(
                lambda line: line.role_id.id == self.id)
            if analytic_approval_role:
                return analytic_approval_role.user_id
            else:
                raise UserError(_('No user assigned to role %s!') % self.display_name)
        return rec
