from odoo import fields, models, api


class ResBankBranch(models.Model):
    _name = "res.bank.branch"
    _description = "Res Bank Branch"

    name = fields.Char(string="Branch Name")
    res_bank_id = fields.Many2one("res.bank", string="Bank")

    _sql_constraints = [("name_uniq", "unique (name)", "Branch must be unique.")]

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get("res_bank_id", False):
            domain = [("res_bank_id", "=", self._context.get("res_bank_id", False))]
        if self._context.get("account_bank_id", False):
            bank_id = self.env["res.bank"].browse(self._context.get("account_bank_id"))
            domain = [("id", "in", bank_id.branches.ids)]
        return super()._search(domain, offset, limit, order, access_rights_uid)
