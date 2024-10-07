from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _project_manager_id_domain(self):
        return [("category_id.name", "ilike", "Project Manager")]

    artwork = fields.Char()
    remark = fields.Char()
    project_manager_id = fields.Many2one(
        comodel_name="res.partner", domain=_project_manager_id_domain
    )
    analytic_plan_id = fields.Many2one(
        comodel_name="account.analytic.plan",
        default=lambda self: self.env.ref("analytic.analytic_plan_projects"),
        compute="_get_default_plan_project",
    )

    def _get_default_plan_project(self):
        for rec in self:
            rec.analytic_plan_id = self.env.ref("analytic.analytic_plan_projects").id

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        res = super(SaleOrder, self)._prepare_invoice()
        if res:
            res["analytic_account_id"] = self.analytic_account_id.id
            res["invoice_date"] = self.date_order
        return res
