# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    branch_id = fields.Many2one('res.bank.branch', string="Branch")
    account_type_id = fields.Many2one('account.types', string="Account Type")
    iban = fields.Char(string="IBAN")

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('check_company_id', False):
            company_id = self.env['res.company'].browse(self._context.get('check_company_id'))
            domain = [('id', 'in', company_id.partner_id.with_context({'check_company_id': False}).bank_ids.ids)]
        return super()._search(domain, offset, limit, order, access_rights_uid)
