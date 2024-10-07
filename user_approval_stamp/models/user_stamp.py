# -*- coding: utf-8 -*-

from odoo import models, fields, api


class UserStamp(models.Model):
    _name = "user.stamp"
    _description = "User Stamp"

    name = fields.Char("Name", required=True)
    stamp_image = fields.Binary("Stamp", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.user.company_id,
        required=True,
        copy=False,
    )
