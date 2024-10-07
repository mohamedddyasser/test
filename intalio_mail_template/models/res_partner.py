from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Contacts"

    check_soa_mail_sent = fields.Boolean("Check SOA Mail Sent")

    def send_soa_from_vendor_mail(self):
        email_values = {"email_to": self.email, "email_from": self.env.user.email}
        email_template = self.env["mail.template"].browse(
            self.env.ref("intalio_mail_template.email_template_vendor_payment_ap").id
        )
        email_template.send_mail(self.id, email_values=email_values, force_send=True)
        self.check_soa_mail_sent = True
