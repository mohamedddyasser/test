from odoo import api, fields, models, _


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    invoiced_draft = fields.Float(compute='_compute_invoiced_draft', string='Draft Invoiced This Month', readonly=True)

    def _compute_invoiced_draft(self):
        if not self:
            return

        query = '''
            SELECT
                move.team_id AS team_id,
                SUM(move.amount_untaxed_signed) AS amount_untaxed_signed
            FROM account_move move
            WHERE move.move_type IN ('out_invoice', 'out_refund', 'out_receipt')
            AND move.team_id IN %s
            AND move.date BETWEEN %s AND %s
            GROUP BY move.team_id
        '''
        today = fields.Date.today()
        params = [tuple(self.ids), fields.Date.to_string(today.replace(day=1)), fields.Date.to_string(today)]
        self._cr.execute(query, params)

        data_map = dict((v[0], v[1]) for v in self._cr.fetchall())
        for team in self:
            team.invoiced_draft = data_map.get(team.id, 0.0)
