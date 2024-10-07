from odoo import models, api, _


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_mail_template(self):
        res = super(AccountMove, self)._get_mail_template()
        if res == "account.email_template_edi_invoice":
            res = "intalio_mail_template.email_template_invoice_customers"
        return res
