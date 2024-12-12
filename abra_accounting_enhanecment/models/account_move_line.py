from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _description = 'Account Move Line'

    claim_percentage = fields.Float(string="Claim Percentage")
