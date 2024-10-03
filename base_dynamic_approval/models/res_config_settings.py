# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    email_resource_calendar_id = fields.Many2one(
        comodel_name='resource.calendar',
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        calendar_value = self.env['ir.config_parameter'].sudo().get_param(
            'base_dynamic_approval.email_resource_calendar_id')
        calendar_value = int(calendar_value) if calendar_value else False
        res.update(
            email_resource_calendar_id=calendar_value
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        email_resource_calendar_id = self.email_resource_calendar_id.id or False
        param.set_param(
            'base_dynamic_approval.email_resource_calendar_id',
            email_resource_calendar_id)
