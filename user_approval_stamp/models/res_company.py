# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = 'Res Company'

    user_stamp_ids = fields.One2many(
        'user.stamp',
        'company_id',
        string='Company Stamps',
        groups="user_approval_stamp.group_allow_approval_with_stamp")
