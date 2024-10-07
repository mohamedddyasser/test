from odoo import models, fields, api


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    trn = fields.Char(
        string="TRN",
        required=False,
    )
