# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        """If invoicing by quantity percentage, modify quantities."""
        res = super()._prepare_invoice_line(**optional_values)
        if self.env.context.get("qty_percentage"):
            if self.env.context.get("qty_percentage") > 100:
                raise UserError("Quantity percentage must be less than 100.")
            precision = self.env["decimal.precision"].precision_get(
                "Product Unit of Measure"
            )
            total_qty = float(
                "%.2f"
                % (self.product_uom_qty - sum(self.invoice_lines.mapped("quantity")))
            )
            quantity = (
                self.product_uom_qty * self.env.context.get("qty_percentage") / 100
            )
            if float_compare(quantity, total_qty, precision_digits=precision) > 0:
                raise UserError(
                    "Quantity percentage must be equal or less than %2.f"
                    % ((total_qty / self.product_uom_qty) * 100)
                )
            res["quantity"] = quantity
            res["claim_percentage"] = self.env.context.get("qty_percentage")
        elif self.env.context.get("qty_percentage") == 0.0:
            raise UserError("Quantity percentage must be more than 0.0")
        return res
