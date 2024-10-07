from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Contacts"

    bank_ids = fields.One2many("res.partner.bank", "partner_id", string="Banks")
    abra_bank_account_id = fields.Many2one(
        comodel_name="res.partner.bank", string="Abra Bank Account"
    )
    trade_license = fields.Char(string="Trade License")
    signatory = fields.Char(string="Signatory")
    job = fields.Char(string="Job ID")

    def customer_approval_unarchive(self):
        if (
            self.activity_type_id.id
            == self.env.ref("customers.approve_customer_activity").id
        ):
            for activity in self.activity_ids:
                activity.action_done()
        self.active = True
