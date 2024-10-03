from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    document_checklist_ids = fields.One2many(comodel_name='sale.order.document.checklist', inverse_name='sale_order_id',
                                             string='Documents')
