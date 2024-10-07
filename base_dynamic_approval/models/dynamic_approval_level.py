# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DynamicApprovalLevel(models.Model):
    _name = "dynamic.approval.level"
    _description = "Approval level"
    _order = "sequence, id"

    approval_id = fields.Many2one(
        comodel_name="dynamic.approval",
    )
    sequence = fields.Integer(
        default=1,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Approver User",
    )
    group_id = fields.Many2one(
        comodel_name="res.groups",
        string="Approver Group",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        readonly=True,
        related="approval_id.company_id",
        store=True,
    )
    hr_officer = fields.Boolean(string="Hr Officer")

    def _get_approval_user(self, model, res):
        """allow to override to select user in other modules"""
        self.ensure_one()
        return self.user_id

    def prepare_approval_request_values(self, model, res):
        """return values for create approval request"""
        self.ensure_one()
        group = self.group_id
        user = self._get_approval_user(model, res)
        if group or user:
            return {
                "res_model": model,
                "res_id": res.id,
                "sequence": self.sequence,
                "user_id": user.id if user else False,
                "group_id": self.group_id.id if self.group_id else False,
                "status": "new",
                "approve_date": False,
                "approved_by": False,
                "dynamic_approve_level_id": self.id,
                "dynamic_approval_id": self.approval_id.id,
            }

        raise UserError(
            _(
                "System can`t find user for user / group for approval type '%s' level sequence number'%s'."
            )
            % (self.approval_id.display_name, self.sequence)
        )

    def _get_approver_source_field(self):
        """
        helper function to return list of fields need to check
        this function can be inherit to add extra fields
        """
        return ["user_id", "group_id"]

    def _check_is_approver_source_chosen(self):
        """return true if at least user_id or group_id has data"""
        for record in self:
            is_approver_source_chosen = False
            if any(
                getattr(record, field) for field in self._get_approver_source_field()
            ):
                is_approver_source_chosen = True
            if not is_approver_source_chosen:
                raise ValidationError(
                    _(
                        "Please choose source of users will approve for level sequence %s"
                    )
                    % record.sequence
                )

    # ORM functions
    @api.model
    def create(self, vals_list):
        """check for approvers source fields"""
        rec = super().create(vals_list)
        rec._check_is_approver_source_chosen()
        return rec

    def write(self, vals):
        """check for approvers source fields"""
        res = super().write(vals)
        self._check_is_approver_source_chosen()
        return res
