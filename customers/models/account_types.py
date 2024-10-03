from odoo import models, fields


class AccountTypes(models.Model):
    _name = 'account.types'
    _description = 'Account Types'

    name = fields.Char(string="Name")

