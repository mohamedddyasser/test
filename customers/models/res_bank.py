from odoo import models, fields


class ResBank(models.Model):
    _name = 'res.bank'
    _description = 'Res Bank'

    branches = fields.Many2many('res.bank.branch', string="Branches", domain=lambda self: list(('res_bank_id', '=', self.id)) )

