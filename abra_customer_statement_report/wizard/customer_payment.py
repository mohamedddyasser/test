from odoo import models, fields, api
from datetime import datetime, date


class CustomerPayment(models.TransientModel):
    _name = "customer.payment.report"
    _description = "Customer Payment Report"

    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer")
    date = fields.Date(string="Date", default=date.today())
    account_move_ids = fields.Many2many(
        comodel_name="account.move", string="Customer Invoice"
    )
    payment_mode = fields.Char(string="Payment Mode")
    instrument_details = fields.Char(string="Instrument Details")
    issued_from = fields.Char(string="Issued From")

    def button_print(self):
        data = {}
        domain = [
            ("state", "=", "posted"),
            ("move_type", "=", "out_invoice"),
            ("amount_residual", ">", 0),
        ]

        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))

        if self.date:
            domain.append(("invoice_date", "<=", self.date))

        if self.account_move_ids:
            domain.append(("id", "in", self.account_move_ids.ids))

        account_move = self.env["account.move"].search(domain, order="id asc")
        account_move_date = []
        wizard_data = []
        total_amount_currency = 0
        if account_move:
            for invoice in account_move:

                total_amount_currency += invoice.currency_id._convert(
                    invoice.amount_residual,
                    self.env.user.company_id.currency_id,
                    self.env.user.company_id,
                    fields.Date.context_today(self),
                )

                account_move_date.append(
                    {
                        "name": invoice.name,
                        "invoice_date": (
                            datetime.strptime(
                                str(invoice.invoice_date), "%Y-%m-%d"
                            ).strftime("%d-%b-%Y")
                            if invoice.invoice_date
                            else ""
                        ),
                        "amount_residual": str(invoice.amount_residual)
                        + str(" ")
                        + str(invoice.currency_id.name),
                    }
                )

        wizard_data.append(
            {
                "date": (
                    datetime.strptime(str(self.date), "%Y-%m-%d").strftime("%d-%b-%Y")
                    if self.date
                    else ""
                ),
                "partner_id": self.partner_id.id,
                "payment_mode": self.payment_mode,
                "instrument_details": self.instrument_details,
                "issued_from": self.issued_from,
                "total_amount": total_amount_currency,
                "total_amount_currency": str(self.env.user.company_id.currency_id.name)
                + " "
                + str(total_amount_currency),
            }
        )

        data["wizard_data"] = wizard_data
        data["account_move_date"] = account_move_date

        return self.env.ref(
            "abra_customer_statement_report.customer_payment_report_pdf"
        ).report_action(self, data=data)


class CustomerPaymentReport(models.AbstractModel):
    _name = "report.abra_customer_statement_report.customer_payment_report"

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env["ir.actions.report"]
        report = report_obj._get_report_from_name(
            "abra_customer_statement_report.customer_payment_report"
        )
        account_move_date = data.get("account_move_date")
        wizard_data = data.get("wizard_data")
        return {
            "doc_ids": self._ids,
            "doc_model": report.model,
            "docs": self,
            "account_move_date": account_move_date,
            "wizard_data": wizard_data,
        }
