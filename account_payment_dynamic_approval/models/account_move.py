# -*- coding: utf-8 -*-
from odoo import _, models, fields, api
from odoo.exceptions import UserError
import ast


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "dynamic.approval.mixin"]
    _state_from = ["draft", "under_approval"]
    _state_to = "posted"

    payment_counter = fields.Integer(
        string="Payments",
        compute="get_payments_count",
    )
    register_payment_invisible = fields.Boolean(string="", compute=None)

    # state = fields.Selection(
    #     selection=[
    #         ('under_approval', 'Under Approval'),
    #         ('draft', 'Approved & Draft'),
    #         ('posted', 'Posted'),
    #         ('sent', 'Sent'),
    #         ('reconciled', 'Reconciled'),
    #         ('cancel', 'Cancelled'),
    #     ],
    #     string='Status',
    #     required=True,
    #     readonly=True,
    #     copy=False,
    #     tracking=True,
    #     default='under_approval',
    # )

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("under_approval", "Under Approval"),
            ("posted", "Posted"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default="draft",
    )

    original_state = fields.Selection(related="state", tracking=True)
    dynamic_approval_state = fields.Selection(related="state", tracking=True)
    state2 = fields.Selection(related="state", tracking=0)

    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        compute="_compute_journal_id",
        store=True,
        readonly=False,
        precompute=True,
        required=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
        domain="[('id', 'in', suitable_journal_ids)]",
    )
    # ref = fields.Char(string='Reference', readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date(
        string="Date",
        index=True,
        compute="_compute_date",
        store=True,
        required=True,
        readonly=False,
        precompute=True,
        default=fields.Date.context_today,
        copy=False,
        tracking=True,
    )
    payment_method_id = fields.Many2one(
        "account.payment.method",
        string="Payment Method",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Manual: Get paid by cash, check or any other method outside of Odoo.\n"
        "Electronic: Get paid automatically through a payment acquirer by requesting a transaction on a card saved by the customer when buying or subscribing online (payment token).\n"
        "Check: Pay bill by check and print it from Odoo.\n"
        "Batch Deposit: Encase several customer checks at once by generating a batch deposit to submit to your bank. When encoding the bank statement in Odoo, you are suggested to reconcile the transaction with the batch deposit.To enable batch deposit, module account_batch_payment must be installed.\n"
        "SEPA Credit Transfer: Pay bill from a SEPA Credit Transfer file you submit to your bank. To enable sepa credit transfer, module account_sepa must be installed ",
    )

    reconciled_invoice_payments_ids = fields.Many2many(
        "account.payment",
        string="Reconciled Payments",
        relation="account_payment_bill_reconciled_rel",
        help="Bills with journal items reconciled with this payments.",
    )

    reconciled_bill_payments_ids = fields.Many2many(
        "account.payment",
        string="Reconciled Payments",
        relation="account_payment_bill_reconciled_rel",
        help="Invoices with journal items reconciled with this payments.",
    )

    # auto_reconcile_lines = fields.One2many('account.auto.reconcile', 'move_id')

    def get_payments_reconciled(self):

        return {
            "name": "Payments",
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [
                (
                    "id",
                    "in",
                    (
                        self.reconciled_bill_payments_ids
                        | self.reconciled_bill_payments_ids
                    ).ids,
                )
            ],
        }

    reconciled_payments_count = fields.Integer(compute="get_reconciled_payments_count")

    def action_post(self):
        res = super().action_post()
        # self.name = '/'.join([self.journal_id.code] + self.name.split('/')[1:])
        return res

    def get_reconciled_payments_count(self):
        for rec in self:
            rec.reconciled_payments_count = len(
                rec.reconciled_bill_payments_ids | rec.reconciled_bill_payments_ids
            )

    @api.depends(
        "posted_before", "state", "journal_id", "date", "move_type", "payment_id"
    )
    def _compute_name(self):
        self = self.sorted(lambda m: (m.date, m.ref or "", m._origin.id))

        for move in self:
            if move.state == "cancel":
                continue

            move_has_name = move.name and move.name != "/"
            if (
                (move_has_name or move.state != "posted")
                and move.move_type != "out_invoice"
            ) or (
                (move_has_name or move.state != "under_approval")
                and move.move_type == "out_invoice"
            ):
                if not move.posted_before and not move._sequence_matches_date():
                    if move._get_last_sequence():
                        # The name does not match the date and the move is not the first in the period:
                        # Reset to draft
                        move.name = False
                        continue
                else:
                    if (
                        move_has_name
                        and move.posted_before
                        or not move_has_name
                        and move._get_last_sequence()
                    ):
                        # The move either
                        # - has a name and was posted before, or
                        # - doesn't have a name, but is not the first in the period
                        # so we don't recompute the name
                        continue
            if move.date and (not move_has_name or not move._sequence_matches_date()):
                move._set_next_sequence()

        self.filtered(lambda m: not m.name and not move.quick_edit_mode).name = "/"
        self._inverse_name()

    # def get_registered_payments(self):
    #
    #     return {
    #         'name': 'Payments',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'account.payment',
    #         'view_mode': 'tree,form',
    #         'target': 'current',
    #         'domain': [('id', 'in', (self.auto_reconcile_lines.filtered_domain(
    #             [
    #                 ('move_id', '=', self.id),
    #                 ('is_reconciled', '=', False),
    #             ]
    #         )).mapped('payment_id').ids)],
    #     }

    # registered_payments_count = fields.Integer(compute='get_registered_payments_count')

    # def get_registered_payments_count(self):
    #     for rec in self:
    #         rec.registered_payments_count = len(
    #             rec.auto_reconcile_lines.filtered_domain(
    #                 [
    #                     ('payment_id', '!=', False),
    #                     ('move_id', '=', rec.id),
    #                     ('is_reconciled', '=', False),
    #                 ]
    #             )
    #         )

    # def check_register_payment_invisible(self):
    #     for rec in self:
    #         if sum(self.env['account.payment'].search(
    #                 [('duplicated_ref_ids', 'in', rec.id), ('state', '!=', 'cancelled')]).mapped(
    #             'amount')) >= rec.amount_total:
    #             rec.register_payment_invisible = True
    #         else:
    #             rec.register_payment_invisible = False

    def get_payments_count(self):
        for rec in self:
            rec.payment_counter = len(
                self.env["account.payment"].search(
                    [
                        ("partner_id", "=", rec.partner_id.id),
                        ("is_reconciled", "=", False),
                    ]
                )
            )

    def get_payments_created(self):
        return {
            "name": "Payments",
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [
                ("partner_id", "=", self.partner_id.id),
                ("is_reconciled", "=", False),
            ],
        }

    def _get_under_validation_exceptions(self):
        exception_list = super()._get_under_validation_exceptions()
        if self._name == "account.move":
            move_exception_list = [
                "needed_terms_dirty",
                "show_original_buttons",
                "custom_is_confirm",
                "warn_msg",
                "invoice_line_ids",
                "line_ids",
                "tax_totals",
                "amount_untaxed",
                "amount_tax",
                "name" "amount_total",
                "amount_residual",
                "amount_untaxed_signed",
                "amount_tax_signed",
                "amount_total_signed",
                "amount_residual_signed",
                "amount_total_in_currency_signed",
                "needed_terms_dirty",
                "sequence_prefix",
                "sequence_number",
            ]
            exception_list.extend(move_exception_list)
        return exception_list

    def _get_after_validation_exceptions(self):
        exception_list = super()._get_after_validation_exceptions()
        if self._name == "account.move":
            move_exception_list = [
                "needed_terms_dirty",
                "show_original_buttons",
                "custom_is_confirm",
                "warn_msg",
                "message_main_attachment_id",
                "is_move_sent",
                "access_token",
                "send_and_print_values",
            ]
            exception_list.extend(move_exception_list)
        return exception_list

    # def _run_final_approve_function(self):
    #     res = super(AccountMove, self.with_context(force_dynamic_validation=True))._run_final_approve_function()
    #     self.sudo().with_context(force_dynamic_validation=True).action_post()
    #     return res

    reconciled_payments_ids = fields.Many2many("account.payment", store=0)

    def button_cancel(self):
        return super(
            AccountMove, self.with_context(force_dynamic_validation=True)
        ).button_cancel()

    def button_draft(self):
        return super(
            AccountMove, self.with_context(force_dynamic_validation=True)
        ).button_draft()

    # vendor_id = fields.Many2one('res.partner', related='partner_id', readonly=0, store=1)

    def test(self):
        # print(self.dynamic_approval_id.approval_condition_ids.mapped('name'))
        # d = self.dynamic_approval_id.approval_condition_ids.mapped('filter_domain')
        # print(d[0])
        # print(self.search(ast.literal_eval(d[0]) if d else []))
        print(self.show_original_buttons)

    # partner_id2 = fields.Many2one('res.partner', compute='compute_vendor', inverse='inverse_vendor')
    #
    # def compute_vendor(self):
    #     for rec in self:
    #         rec.partner_id2 = rec.partner_id
    #
    # def inverse_vendor(self):
    #     for rec in self:
    #         rec.partner_id = rec.partner_id2

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        for invoice in self:
            wrong_lines = invoice.is_invoice() and invoice.line_ids.filtered(
                lambda aml: aml.partner_id != invoice.commercial_partner_id
                and aml.display_type not in ("line_note", "line_section")
            )
            if wrong_lines:
                wrong_lines.write({"partner_id": invoice.commercial_partner_id.id})
        if vals.get("state") == "under_approval":
            self.flush_recordset()  # Ensure that the name is correctly computed before it is used to generate the hash
            for move in self.filtered(
                lambda m: m.restrict_mode_hash_table
                and not (m.secure_sequence_number or m.inalterable_hash)
            ).sorted(lambda m: (m.date, m.ref or "", m.id)):
                new_number = move.journal_id.secure_sequence_id.next_by_id()
                res |= super(AccountMove, move).write(
                    {
                        "secure_sequence_number": new_number,
                        "inalterable_hash": move._get_new_hash(new_number),
                    }
                )
        return res
