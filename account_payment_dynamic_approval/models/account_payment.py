# -*- coding: utf-8 -*-
""" inherit account.payment """
from odoo import _, models, fields
from odoo.exceptions import UserError
import ast


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment', 'dynamic.approval.mixin']
    _state_from = ['draft', 'under_approval']
    _state_to = 'posted'

    def run_under_approval_action(self):
        for rec in self:
            rec.write({'state': 'under_approval'})

    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money')],
        string='Payment Type', required=True, readonly=True, default="outbound",
        states={'draft': [('readonly', False)]})
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], tracking=True, readonly=True,
                                    states={'draft': [('readonly', False)]})

    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 )

    amount = fields.Monetary(string='Amount', required=True, readonly=True,
                             states={'draft': [('readonly', False)]},
                             tracking=True)

    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env.company.currency_id)
    invisible_approval_request = fields.Boolean()

    reconciled_bill_ids = fields.Many2many('account.move', string="Reconciled Bills", store=1,
                                           relation='account_payment_bill_reconciled_rel',
                                           help="Invoices whose journal items have been reconciled with these payments.")

    reconciled_invoice_ids = fields.Many2many('account.move', string="Reconciled Invoices", store=1,
                                              relation='account_payment_invoice_reconciled_rel',
                                              help="Invoices whose journal items have been reconciled with these payments.")

    # show_original_buttons = fields.Boolean(compute='_compute_show_original_buttons')

    def _compute_show_original_buttons(self):
        dynamic_approval = self.env['dynamic.approval'].search([('model_id', '=', 'account.payment')], limit=1)
        payments = self.env['account.payment']
        for i in dynamic_approval.approval_condition_ids:
            payments |= self.search([]).filtered_domain(ast.literal_eval(i.filter_domain))

        for rec in self:
            rec.show_original_buttons = rec not in payments

    def action_post(self):
        res = super().action_post()
        # self.name = '/'.join([self.journal_id.code] + self.name.split('/')[1:])
        return res

    def action_register_payment(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''

        return {
            'name': _('Register Payment'),
            'res_model': len(active_ids) == 1 and 'account.payment' or 'account.payment.register',
            'view_mode': 'form',
            'view_id': len(active_ids) != 1 and self.env.ref(
                'account.view_account_payment_form_multi').id or self.env.ref(
                'account_payment_dynamic_approval.view_account_payment_invoice_form_inherit_to_approve').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    # def action_draft(self):
    #     res = super().action_draft()
    #     self.remove_approval_requests()
    #     self.state = 'draft'
    #     self.invisible_approval_request = False
    #     return res

    def cancel(self):
        res = super().cancel()
        self.mapped('dynamic_approve_request_ids').write({
            'status': 'rejected',
            'approve_date': False,
            'approved_by': False,
        })
        return res

    def post(self):
        """ override to restrict user to confirm if there is workflow """
        res = super().post()
        if self.mapped('dynamic_approve_request_ids') and \
                self.mapped('dynamic_approve_request_ids').filtered(lambda request: request.status != 'approved'):
            raise UserError(
                _('You can not confirm order, There are pending approval.'))
        for record in self:
            activity = record._get_user_approval_activities()
            if activity:
                activity.action_feedback()
        return res

    def _get_after_validation_exceptions(self):
        exception_list = super()._get_after_validation_exceptions()
        if self._name == 'account.payment':
            move_exception_list = ['is_move_sent', 'batch_payment_id']
            exception_list.extend(move_exception_list)
        return exception_list


    # def pre_action_dynamic_approval_request(self):
    #     for rec in self:
    #         rec.invisible_approval_request = True
    #         rec.action_dynamic_approval_request()

    # def _get_after_validation_exceptions(self):
    #     exception_list = super()._get_after_validation_exceptions()
    #     if self._name == 'account.payment':
    #         payment_exception_list = ['line_ids']
    #         exception_list.extend(payment_exception_list)
    #     return exception_list

    # def _run_final_approve_function(self):
    #     res = super(AccountPayment, self.with_context(force_dynamic_validation=True))._run_final_approve_function()
    #     self.sudo().with_context(force_dynamic_validation=True).action_post()
    #     # print('zzzzzzzzzzzzzzzzzzzzzzzzzzzz')
    #     # print(self.env['account.auto.reconcile'].search(
    #     #     [('payment_id', '=', self.id), ('is_reconciled', '=', False)]))
    #     for r in self.env['account.auto.reconcile'].search(
    #             [('payment_id', '=', self.id), ('is_reconciled', '=', False)]):
    #         r.line_ids.sudo().with_context(force_dynamic_validation=True).reconcile()
    #         r.is_reconciled = True
    #     return res

    def _reconcile(self):
        for r in self.env['account.auto.reconcile'].search(
                [('payment_id', '=', self.id), ('is_reconciled', '=', False)]):
            r.line_ids.sudo().with_context(force_dynamic_validation=True).reconcile()
            r.is_reconciled = True


class AutoReconcile(models.Model):
    _name = 'account.auto.reconcile'

    line_ids = fields.One2many('account.move.line', 'auto_reconcile_id')
    move_id = fields.Many2one('account.move')
    payment_id = fields.Many2one('account.payment')
    is_reconciled = fields.Boolean()

    def write(self, vals):
        # Call the original method to get the usual behavior
        res = super().write(vals)

        # Check if payment_id is being set to None
        if 'payment_id' in vals and not vals['payment_id']:
            # Delete the records where payment_id is set to None
            self.filtered(lambda r: r.payment_id is None).unlink()

        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    auto_reconcile_id = fields.Many2one('account.auto.reconcile')


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        #### overwrite just to stop posting the payment
        self.ensure_one()
        batches = self._get_batches()
        first_batch_result = batches[0]
        edit_mode = self.can_edit_wizard and (len(first_batch_result['lines']) == 1 or self.group_payment)
        to_process = []

        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard(first_batch_result)
            to_process.append({
                'create_vals': payment_vals,
                'to_reconcile': first_batch_result['lines'],
                'batch': first_batch_result,
            })
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'payment_values': {
                                **batch_result['payment_values'],
                                'payment_type': 'inbound' if line.balance > 0 else 'outbound'
                            },
                            'lines': line,
                        })
                batches = new_batches

            for batch_result in batches:
                to_process.append({
                    'create_vals': self._create_payment_vals_from_batch(batch_result),
                    'to_reconcile': batch_result['lines'],
                    'batch': batch_result,
                })

        payments = self._init_payments(to_process, edit_mode=edit_mode)
        # self._post_payments(to_process, edit_mode=edit_mode)
        self._reconcile_payments(to_process, edit_mode=edit_mode)
        return payments

    def _reconcile_payments(self, to_process, edit_mode=False):
        res = super()._reconcile_payments(to_process, edit_mode=edit_mode)
        """ Reconcile the payments.

        :param to_process:  A list of python dictionary, one for each payment to create, containing:
                            * create_vals:  The values used for the 'create' method.
                            * to_reconcile: The journal items to perform the reconciliation.
                            * batch:        A python dict containing everything you want about the source journal items
                                            to which a payment will be created (see '_get_batches').
        :param edit_mode:   Is the wizard in edition mode.
        """
        domain = [
            # ('parent_state', '=', 'posted'),
            ('account_type', 'in', ('asset_receivable', 'liability_payable')),
            ('reconciled', '=', False),
        ]
        # move_id = self.line_ids[0].move_id
        moves = self.line_ids.mapped('move_id')
        # print(moves)
        for vals in to_process:
            payment_lines = vals['payment'].line_ids.filtered_domain(domain)
            lines = vals['to_reconcile']

            # moves = vals['payment'].ref.split(' ')
            for move in moves:

                for account in payment_lines.account_id:
                    print(vals['payment'])

                    self.env['account.auto.reconcile'].create({
                        'line_ids': (payment_lines + lines) \
                            .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]).ids,
                        'payment_id': vals['payment'].id,
                        'move_id': move.id,
                    })

        return res
