from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_report_filename(self):
        self.ensure_one()
        if self.analytic_account_id:
            return f'{self.analytic_account_id.code} - {self.analytic_account_id.name}' if self.analytic_account_id.code else f'{self.analytic_account_id.name}'
        return False
