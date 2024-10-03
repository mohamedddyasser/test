# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MailAlias(models.Model):
    _inherit = 'mail.alias'

    apply_dynamic_approval = fields.Boolean()

    # alias_domain = fields.Char('Alias domain', compute='_compute_alias_domain')

    _sql_constraints = [
        ('dynamic_approval_alias_unique', 'UNIQUE (apply_dynamic_approval, alias_model_id)',
         "Can't configure multiple alias for approval cycle on same target model!"),
    ]

    @api.depends('alias_name')
    def _compute_alias_domain(self):
        self.alias_domain = self.env["ir.config_parameter"].sudo().get_param("mail.approvals.amail.domain")

    # @api.depends('alias_name')
    # def _compute_alias_domain(self):
    #     self.alias_domain = self.env["ir.config_parameter"].sudo().get_param("mail.approvals.domain")
