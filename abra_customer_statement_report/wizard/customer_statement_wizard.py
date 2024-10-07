from odoo import models, fields, api
from datetime import datetime, date


class CustomerStatement(models.TransientModel):
    _name = "customer.statement.report"
    _description = "Customer Statement Report"

    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer")
    date = fields.Date(string="Date", default=date.today())
    currency_ids = fields.Many2many(comodel_name="res.currency", string="Currency")

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

        if self.currency_ids:
            domain.append(("currency_id", "in", self.currency_ids.ids))

        account_move = self.env["account.move"].search(domain, order="id asc")
        account_move_date = []
        wizard_data = []
        total_amount_currency = 0
        if account_move:
            for invoice in account_move:

                dif_date = (
                    datetime.strptime(str(invoice.invoice_date_due), "%Y-%m-%d").date()
                    - date.today()
                )

                amount_currency = invoice.currency_id._convert(
                    invoice.amount_residual,
                    self.env.user.company_id.currency_id,
                    self.env.user.company_id,
                    fields.Date.context_today(self),
                )

                total_amount_currency += amount_currency

                # print(amount_currency,"$$$$$$$$$$$$$$$$$$$$$$")
                account_move_date.append(
                    {
                        "invoice_date": (
                            datetime.strptime(
                                str(invoice.invoice_date), "%Y-%m-%d"
                            ).strftime("%d-%b-%Y")
                            if invoice.invoice_date
                            else ""
                        ),
                        "name": invoice.name,
                        "ref": invoice.ref,
                        "analytic_account_id": invoice.analytic_account_id.name,
                        "invoice_payment_term_id": invoice.invoice_payment_term_id.name,
                        "amount_dhs": float(amount_currency),
                        "amount_currency": str(invoice.amount_residual)
                        + str(" ")
                        + str(invoice.currency_id.name),
                        "invoice_date_due": int(dif_date.days),
                        "due_in": (
                            datetime.strptime(
                                str(invoice.invoice_date_due), "%Y-%m-%d"
                            ).strftime("%d-%b-%Y")
                            if invoice.invoice_date_due
                            else ""
                        ),
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
                "total_amount_currency": total_amount_currency,
            }
        )

        data["wizard_data"] = wizard_data
        data["account_move_date"] = account_move_date
        return self.env.ref(
            "abra_customer_statement_report.customer_statement_report_pdf"
        ).report_action(self, data=data)


class CustomerStatementReport(models.AbstractModel):
    _name = "report.abra_customer_statement_report.customer_statement_report"

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env["ir.actions.report"]
        report = report_obj._get_report_from_name(
            "abra_customer_statement_report.customer_statement_report"
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
