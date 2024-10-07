from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    credit_move_id = fields.Many2one(
        comodel_name="account.move", compute="compute_credit_move"
    )

    @api.depends("move_type", "name")
    def compute_credit_move(self):
        for rec in self:
            rec.credit_move_id = False
            if rec.move_type == "out_refund":
                account_move = self.env["account.move"].search(
                    [
                        ("reversal_move_id", "in", rec.id),
                        ("move_type", "=", "out_invoice"),
                    ]
                )
                if account_move:
                    rec.credit_move_id = account_move.id

    @api.model
    def get_views(self, views, options=None):
        res = super(AccountMoveInherit, self).get_views(views, options)

        if (
            options.get("action_id")
            and self.env["ir.actions.act_window"]
            .sudo()
            .browse(options.get("action_id"))
            .xml_id
            != "account.action_move_out_refund_type"
        ):

            def get_report_id():
                return self.env["ir.model.data"]._xmlid_to_res_id(
                    "abra_credit_note.account_tax_credit_note_report",
                    raise_if_not_found=False,
                )

            for view_data in res["views"].values():

                print_data_list = view_data.get("toolbar", {}).get("print")
                if print_data_list:

                    report_id = get_report_id()
                    if report_id:
                        view_data["toolbar"]["print"] = [
                            print_data
                            for print_data in print_data_list
                            if print_data["id"] != report_id
                        ]

        return res
