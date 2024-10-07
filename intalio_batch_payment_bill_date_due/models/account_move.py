from odoo import models, api, _


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_move_display_name(self, show_ref=False):
        res = super(AccountMove, self)._get_move_display_name(show_ref)
        if self.env.context.get("default_batch_type", False) == "outbound":
            res += f" ({self.invoice_date_due})" if self.invoice_date_due else ""
        return res

    @api.depends("partner_id", "date", "state", "move_type")
    @api.depends_context("input_full_display_name", "default_batch_type")
    def _compute_display_name(self):
        for move in self:
            if self.env.context.get("default_batch_type", False) == "outbound":
                move.display_name = move._get_move_display_name(show_ref=False)
            else:
                return super(AccountMove, self)._compute_display_name()
