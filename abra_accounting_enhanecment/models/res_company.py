from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = 'Res Company'

    stamp = fields.Binary(string="Stamp")
    company_info = fields.Char(string="Company Info", translate=True)

