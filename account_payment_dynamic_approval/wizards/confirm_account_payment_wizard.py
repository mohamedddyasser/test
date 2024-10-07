from odoo import models, fields


class ConfirmaccountpaymentWizard(models.TransientModel):
    _name = "confirm.account.payment.wizard"
    _description = "Confirm account payment Without Approval Wizard"

    name = fields.Char(
        default="There is no approval workflow found, Are you sure to confirm order without approvals cycle?",
    )

    def action_confirm_order(self):
        if self._context.get("active_model") == "account.payment":
            order = self.env["account.payment"].browse(self._context.get("active_id"))
            order.button_confirm()
