from odoo import models, fields, api


class MailActivity(models.Model):
    _inherit = "mail.activity"
    _description = "Activity"

    @api.depends("res_model", "res_id", "user_id")
    def _compute_can_write(self):
        valid_records = self._filter_access_rules("write")
        for record in self:
            if record.user_id.id == self.env.user.id:
                record.can_write = record in valid_records
            else:
                record.can_write = False
