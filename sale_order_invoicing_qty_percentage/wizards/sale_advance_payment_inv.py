from odoo import fields, models, api


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(
        # Added before "Down payment (percentage)" option
        selection_add=[
            ("qty_percentage", "Percentage of the quantity"),
            ("percentage",),
        ],
        ondelete={"qty_percentage": "set default"},
    )
    qty_percentage = fields.Float(string="Quantity percentage")

    # def _get_claim_percentage_remaining(self):
    #     for rec in self:
    #         sale_order = rec.env['sale.order'].browse(self._context.get('active_id'))

    claim_percentage_remaining = fields.Float(string="Claim Percentage Remaining")

    def _get_so_claim_percentage_remaining(self):
        so_claim_percentage_remaining = (
            self.env["sale.order"]
            .browse(self._context.get("active_id"))
            .claim_percentage_remaining
        )
        return (
            (100.00 - so_claim_percentage_remaining)
            if so_claim_percentage_remaining != 0.00
            else 100.00
        )

    @api.onchange("qty_percentage")
    def _change_qty_percentage(self):
        so_claim_percentage_remaining = self._get_so_claim_percentage_remaining()
        claim_percentage_remaining = so_claim_percentage_remaining - self.qty_percentage
        self.claim_percentage_remaining = (
            claim_percentage_remaining if claim_percentage_remaining > 0 else 0
        )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if res:
            res["claim_percentage_remaining"] = (
                self._get_so_claim_percentage_remaining()
            )
        return res

    def create_invoices(self):
        """Inject context key for later use that information to modify quantities
        and switch the invoiced method back to regular one for using the normal flow.
        """
        if self.advance_payment_method == "qty_percentage":
            self = self.with_context(qty_percentage=self.qty_percentage)
            self.advance_payment_method = "delivered"
        return super().create_invoices()
