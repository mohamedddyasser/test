# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WorkFlowSelect(models.TransientModel):
    _name = "work.flow.select"
    _description = "Work Flow Select"

    approval_id = fields.Many2one(
        comodel_name="dynamic.approval", string="Work Flow", required=True
    )
    approval_ids = fields.Many2many(
        comodel_name="dynamic.approval",
        string="Work Flows",
        compute="compute_approval_ids",
        store=True,
    )
    res_model = fields.Char(
        string="",
        required=False,
    )
    res_id = fields.Char(
        string="",
        required=False,
    )

    @api.depends("res_model", "res_id")
    def compute_approval_ids(self):
        record = self.env[self.res_model].browse(int(self.res_id))
        company = (
            getattr(record, record._company_field) if record._company_field else False
        )
        matched_approval = self.env["dynamic.approval"].get_matched_approval(
            model=record._name, res=record, company=company
        )
        self.approval_ids = matched_approval.ids

    def action_apply(self):
        record = self.env[self.res_model].browse(int(self.res_id))
        approval_request_values = self.approval_id._prepare_approval_request_values(
            self.res_model, record
        )
        self.env["dynamic.approval.request"].create(approval_request_values)
        record.apply_dynamic_approval(self.approval_id)
