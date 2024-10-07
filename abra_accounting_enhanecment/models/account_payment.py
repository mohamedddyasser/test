from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'Account Payment'

    # cheque_number = fields.Char(string="Cheque No")

    # if found reconciled bills or invoices that connected to payment will set payment memo with bill or
    # invoice payment reference
    @api.depends('move_id.line_ids.matched_debit_ids', 'move_id.line_ids.matched_credit_ids')
    def _compute_stat_buttons_from_reconciliation(self):
        super()._compute_stat_buttons_from_reconciliation()
        stored_payments = self.filtered('id')
        if not stored_payments:
            self.reconciled_invoice_ids = False
            self.reconciled_invoices_count = 0
            self.reconciled_invoices_type = ''
            self.reconciled_bill_ids = False
            self.reconciled_bills_count = 0
            self.reconciled_statement_line_ids = False
            self.reconciled_statement_lines_count = 0
            return
        self._cr.execute('''
            SELECT
                payment.id,
                ARRAY_AGG(DISTINCT invoice.id) AS invoice_ids,
                invoice.move_type
            FROM account_payment payment
            JOIN account_move move ON move.id = payment.move_id
            JOIN account_move_line line ON line.move_id = move.id
            JOIN account_partial_reconcile part ON
                part.debit_move_id = line.id
                OR
                part.credit_move_id = line.id
            JOIN account_move_line counterpart_line ON
                part.debit_move_id = counterpart_line.id
                OR
                part.credit_move_id = counterpart_line.id
            JOIN account_move invoice ON invoice.id = counterpart_line.move_id
            JOIN account_account account ON account.id = line.account_id
            WHERE account.account_type IN ('asset_receivable', 'liability_payable')
                AND payment.id IN %(payment_ids)s
                AND line.id != counterpart_line.id
                AND invoice.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
            GROUP BY payment.id, invoice.move_type
        ''', {
            'payment_ids': tuple(stored_payments.ids)
        })
        query_res = self._cr.dictfetchall()
        invoice_model = self.env['account.move']
        for res in query_res:
            pay = self.browse(res['id'])
            if pay.reconciled_bill_ids or pay.reconciled_invoice_ids:
                invoice_ids = res.get('invoice_ids', [])
                references = [
                    invoice_model.browse(inv).payment_reference or ""
                    for inv in invoice_ids
                ]
                ref = "".join(references)
                if ref:
                    pay.ref = ref

    @api.model
    def get_views(self, views, options=None):
        res = super(AccountPayment, self).get_views(views, options)

        if options and options.get('action_id', False):

            def _is_action_window(xml_id):
                return self.env['ir.actions.act_window'].sudo().browse(options.get('action_id')).xml_id == xml_id

            def _get_report_id(xml_id):
                return self.env['ir.model.data']._xmlid_to_res_id(xml_id, raise_if_not_found=False)

            def _remove_report_action(xml_id):
                for view_data in res['views'].values():
                    print_data_list = view_data.get('toolbar', {}).get('print')
                    if print_data_list:
                        report_id = _get_report_id(xml_id=xml_id)
                        if report_id:
                            view_data['toolbar']['print'] = [print_data for print_data in print_data_list if
                                                             print_data['id'] != report_id]

            if _is_action_window(xml_id='account.action_account_payments_payable'):
                _remove_report_action(xml_id="abra_accounting_enhanecment.action_receipt_voucher_account_payment")

            elif _is_action_window(xml_id="account.action_account_payments"):
                _remove_report_action(xml_id="account.action_report_payment_receipt")

        return res
