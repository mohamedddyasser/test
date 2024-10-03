from odoo import models, _
from odoo.exceptions import ValidationError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def _create_invoices(self, sale_orders):
        for order in sale_orders:
            if not order.document_checklist_ids or any(not doc.attachment_ids for doc in order.document_checklist_ids):
                raise ValidationError(_("Missing Required Document"))

        return super(SaleAdvancePaymentInv, self)._create_invoices(sale_orders)
