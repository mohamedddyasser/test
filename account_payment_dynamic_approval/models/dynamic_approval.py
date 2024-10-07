# -*- coding: utf-8 -*-
from odoo import models, api


class DynamicApproval(models.Model):
    _inherit = "dynamic.approval"

    @api.model
    def _get_approval_validation_model_names(self):
        """add model account.payment to model options"""
        res = super()._get_approval_validation_model_names()
        # res.append('account.payment')
        res.append("account.move")
        res.append("account.batch.payment")
        return res
