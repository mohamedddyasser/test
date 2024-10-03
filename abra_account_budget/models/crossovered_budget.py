from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class CrossoveredBudgetInherit(models.Model):
    _inherit = 'crossovered.budget'

    @api.model
    def create(self, vals):
        res = super(CrossoveredBudgetInherit, self).create(vals)
        if res:

            for line in res.crossovered_budget_line:
                account_budget_post = self.env['account.budget.post'].search(
                    [('account_ids', 'in', line.account_id.id)], limit=1)

                if not account_budget_post and line.account_id:
                    line.general_budget_id = self.env['account.budget.post'].create({
                        'name': line.account_id.display_name,
                        'budget_id': res.id,
                        'account_ids': [(4, line.account_id.id)]
                    }).id
                else:
                    if line.general_budget_id:
                        line.general_budget_id.budget_id = res.id

        return res

    def write(self, values):
        res = super(CrossoveredBudgetInherit, self).write(values)
        if "crossovered_budget_line" in values and values['crossovered_budget_line']:

            for line in self.crossovered_budget_line:
                account_budget_post = self.env['account.budget.post'].search(
                    [('account_ids', 'in', line.account_id.id)], limit=1)

                if not account_budget_post and line.account_id:
                    line.general_budget_id = self.env['account.budget.post'].create({
                        'name': line.account_id.display_name,
                        'budget_id': self.id,
                        'account_ids': [(4, line.account_id.id)]
                    }).id
                else:
                    if line.general_budget_id:
                        line.general_budget_id.budget_id = self.id

        return res


class CrossoveredBudgetLinesInherit(models.Model):
    _inherit = 'crossovered.budget.lines'

    account_id = fields.Many2one(comodel_name="account.account", string="Account")
    code = fields.Char(string="Code", related='account_id.code')

    # @api.constrains('general_budget_id', 'analytic_account_id')
    # def _must_have_analytical_or_budgetary_or_both(self):
    #     for record in self:
    #         if not record.analytic_account_id and not record.general_budget_id:
    #             pass


class AccountBudgetPostInherit(models.Model):
    _inherit = 'account.budget.post'

    budget_id = fields.Many2one('crossovered.budget', string="Budget")

    @api.constrains('account_ids')
    def check_account_budget_line(self):

        if len(self.account_ids.ids) > 1:
            raise ValidationError("Budgetary Positions Must Be Have only one Account")

        account_budget_post = self.env['account.budget.post'].search(
            [('account_ids', 'in', self.account_ids.ids), ('id', '!=', self.id)])
        if account_budget_post:
            raise ValidationError("Budgetary Positions Must Be Have Unique Account")
