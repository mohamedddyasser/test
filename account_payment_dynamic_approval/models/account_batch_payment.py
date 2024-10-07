from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountBatchPayment(models.Model):
    _name = "account.batch.payment"
    _inherit = ["account.batch.payment", "dynamic.approval.mixin"]
    _state_from = ["draft", "under_approval"]
    _state_to = "sent"

    state = fields.Selection(
        [
            ("draft", "New"),
            ("under_approval", "Under Approval"),
            ("sent", "Sent"),
            ("reconciled", "Reconciled"),
            ("cancel", "Cancelled"),
        ],
        store=True,
        compute="_compute_state",
        default="draft",
        tracking=True,
    )
    original_state = fields.Selection(related="state")
    dynamic_approval_state = fields.Selection(related="state")
    under_approval_check = fields.Boolean(string="Under Approval Check")
    cancel_check = fields.Boolean(string="cancel Check")
    confirm_check = fields.Boolean(string="confirm Check")

    @api.depends(
        "payment_ids.move_id.is_move_sent",
        "payment_ids.is_matched",
        "cancel_check",
        "under_approval_check",
        "confirm_check",
    )
    def _compute_state(self):
        for batch in self:
            batch.state = "draft"
            if self.under_approval_check:
                batch.state = "under_approval"
                if batch.payment_ids and all(
                    pay.is_matched and pay.is_move_sent for pay in batch.payment_ids
                ):
                    batch.state = "reconciled"
                if batch.confirm_check and batch.state == "under_approval":
                    batch.validate_batch_button()
                    if (
                        batch.payment_ids
                        and all(pay.is_move_sent for pay in batch.payment_ids)
                        and self.confirm_check
                    ):
                        batch.state = "sent"
            if self.cancel_check:
                batch.state = "cancel"

    def action_move_batch_payment_to_under_approval(self):
        for rec in self:
            rec.under_approval_check = True

    def action_move_batch_payment_to_draft(self):
        for rec in self:
            rec.under_approval_check = False
            rec.cancel_check = False
            rec.confirm_check = False

    def action_move_batch_payment_cancel(self):
        for rec in self:
            rec.cancel_check = True

    def action_move_batch_payment_confirm(self):
        for rec in self:
            rec.confirm_check = True

    def action_reset_draft(self):
        for batch_payment in self:
            batch_payment.with_context(force_dynamic_validation=True).write(
                {
                    "state": "draft",
                    "need_validation": True,
                    "dynamic_approve_request_ids": [(5,)],
                    "under_approval_check": False,
                    "cancel_check": False,
                    "confirm_check": False,
                }
            )

    def _get_under_validation_exceptions(self):
        exception_list = super()._get_under_validation_exceptions()
        if self._name == "account.batch.payment":
            move_exception_list = ["under_approval_check"]
            exception_list.extend(move_exception_list)
        return exception_list
