# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.exceptions import UserError
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "Sale Order"

    claim_percentage_remaining = fields.Float(
        compute="_compute_claim_percentage_remaining",
        string="Claim Percentage Remaining",
        default=0.00,
        copy=False,
    )

    def _compute_claim_percentage_remaining(self):
        for sale_order in self:
            percentage_remaining = 0
            for invoice in sale_order.invoice_ids:
                for line in invoice.invoice_line_ids:
                    percentage_remaining += line.claim_percentage
                    break
            sale_order.claim_percentage_remaining = percentage_remaining
