from num2words import num2words
from lxml import etree
from odoo.tools.misc import frozendict
from odoo import models, fields, _, api
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'Account Move'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Project")
    job = fields.Char(string="Job ID", related='analytic_account_id.code')
    number_ref = fields.Char(string="Number Reference")
    check_invoice_info_duplicate = fields.Boolean("invoice info duplicate")

    def button_draft(self):
        self._check_draftable()
        # We remove all the analytics entries for this journal
        self.mapped('line_ids.analytic_line_ids').unlink()
        self.mapped('line_ids').remove_move_reconcile()
        self.write({'state': 'draft', 'is_move_sent': False})

    def button_cancel(self):
        # Shortcut to move from posted to cancelled directly. This is useful for E-invoices that must not be changed
        # when sent to the government.
        moves_to_reset_draft = self.filtered(lambda x: x.state not in ['draft', 'cancel'])
        if moves_to_reset_draft:
            moves_to_reset_draft.button_draft()

        if any(move.state != 'draft' for move in self):
            raise UserError(_("Only draft journal entries can be cancelled."))

        self.write({'auto_post': 'no', 'state': 'cancel'})

    @api.onchange('partner_id')
    def get_recipet_bank_from_customer(self):
        if self.partner_id and self.move_type == 'out_invoice':
            self.partner_bank_id = self.partner_id.abra_bank_account_id.id

    @api.constrains('partner_id', 'number_ref', 'amount_total')
    def display_warning_when_duplicated_bills(self):
        for rec in self:
            if rec.move_type == 'in_invoice':
                bills_to_same_vendor = rec.env['account.move'].search([('move_type', '=', 'in_invoice'),
                                                                        ('partner_id', '=', rec.partner_id.id),
                                                                        ('number_ref', '=', rec.number_ref),
                                                                        ('amount_total', '=', rec.amount_total), ])
                if len(bills_to_same_vendor) > 1:
                    rec.check_invoice_info_duplicate = True
                else:
                    rec.check_invoice_info_duplicate = False