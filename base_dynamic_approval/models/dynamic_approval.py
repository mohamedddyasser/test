# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DynamicApproval(models.Model):
    _name = "dynamic.approval"
    _description = "Approval Configuration"
    _order = "sequence, id"

    @api.model
    def _get_approval_validation_model_names(self):
        res = []
        return res

    name = fields.Char(
        string="Description",
        required=True,
        translate=True,
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Referenced Document",
        required=True,
        ondelete="cascade",
        domain=lambda self: [
            ("model", "in", self._get_approval_validation_model_names())
        ],
    )
    model = fields.Char(related="model_id.model", index=True, store=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(
        default=10,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )
    approval_condition_ids = fields.One2many(
        comodel_name="dynamic.approval.condition",
        inverse_name="approval_id",
        string="Conditions",
        copy=True,
    )
    approval_condition_number = fields.Integer(
        compute="_compute_approval_condition_number"
    )
    approval_level_ids = fields.One2many(
        comodel_name="dynamic.approval.level",
        inverse_name="approval_id",
        string="Levels",
        copy=True,
    )
    # fields used in under approval stage
    email_template_to_approve_id = fields.Many2one(
        comodel_name="mail.template",
    )
    need_create_activity_to_approve = fields.Boolean(
        default=True,
    )
    dynamic_approve = fields.Boolean(
        default=True,
    )

    to_approve_server_action_id = fields.Many2one(
        comodel_name="ir.actions.server",
    )
    reminder_period_to_approve = fields.Integer(
        help="Set trigger duration after request approval pending",
        default=5,
    )
    reminder_pending_approver_email_template_id = fields.Many2one(
        comodel_name="mail.template",
    )
    # fields user after last approve
    default_notify_user_field_after_final_approve_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Default user fields after final approval (Activity)",
    )
    notify_user_field_after_final_approve_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="approval_notify_after_final_approve_field_rel",
        string="Notified users fields after final approve",
    )
    email_template_after_final_approve_id = fields.Many2one(
        comodel_name="mail.template",
    )
    after_final_approve_server_action_id = fields.Many2one(
        comodel_name="ir.actions.server",
    )

    # fields used when user reject
    notify_user_field_rejection_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="approval_notify_reject_field_rel",
        string="Notified users fields for rejection",
    )
    default_notify_user_field_rejection_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Default user field for rejection (Activity)",
    )
    rejection_email_template_id = fields.Many2one(
        comodel_name="mail.template",
    )
    need_notify_rejection_approved_user = fields.Boolean()
    rejection_server_action_id = fields.Many2one(
        comodel_name="ir.actions.server",
    )
    # fields used when user recall
    notify_user_field_recall_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="approval_notify_recall_field_rel",
        string="Notified users fields for recall",
    )
    default_notify_user_field_recall_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Default user field for recall (Activity)",
    )
    recall_email_template_id = fields.Many2one(
        comodel_name="mail.template",
    )
    need_notify_recall_approved_user = fields.Boolean()
    recall_server_action_id = fields.Many2one(
        comodel_name="ir.actions.server",
    )
    # fields used when user request approval
    state_under_approval = fields.Char(string="Under Approval Status")

    apply_recall = fields.Boolean()
    skip_order_approval = fields.Boolean()

    @api.constrains("approval_level_ids")
    def allow_for_one_hr_officer_on_levels(self):
        if self.approval_level_ids:
            if (
                len(self.approval_level_ids.filtered(lambda x: x.hr_officer == True))
                > 1
            ):
                raise UserError("Hr Officer must be one person.")

    def _compute_approval_condition_number(self):
        """compute number of conditions to appear in smart button"""
        for record in self:
            record.approval_condition_number = len(record.approval_condition_ids)

    def is_matched_approval(self, res):
        """return True / False based on approval match record condition"""
        self.ensure_one()
        for condition in self.approval_condition_ids:
            if not condition.is_condition_matched(res=res):
                return False
        return True

    def _prepare_approval_request_values(self, model, res):
        """return values for approval request"""
        self.ensure_one()
        return [
            level.prepare_approval_request_values(model=model, res=res)
            for level in self.approval_level_ids
        ]

    @api.model
    def action_set_approver(self, model, res, company=False, manager=None):
        """return approval match record condition"""
        domain = [("model", "=", model), ("approval_level_ids", "!=", False)]
        if company:
            domain += ["|", ("company_id", "=", company.id), ("company_id", "=", False)]
        approvals = self.sudo().search(domain, order="sequence ASC")
        matched_approval = self.env["dynamic.approval"]
        for approval in approvals:
            if approval.is_matched_approval(res=res):
                matched_approval = approval
                break
        if matched_approval:
            approval_request_values = matched_approval._prepare_approval_request_values(
                model, res
            )
            if manager:
                manager_request = approval_request_values[0].copy()
                manager_request["sequence"] = 0
                manager_request["user_id"] = manager.id
                manager_request["group_id"] = None
                approval_request_values.append(manager_request)
            self.env["dynamic.approval.request"].create(approval_request_values)
            # add try to make sure that user inherit dynamic.approval.mixin
        return matched_approval

    def get_matched_approval(self, model, res, company=False):
        """return approval match record condition"""
        domain = [("model", "=", model), ("approval_level_ids", "!=", False)]
        if company:
            domain += ["|", ("company_id", "=", company.id), ("company_id", "=", False)]
        approvals = self.sudo().search(domain, order="sequence ASC")
        matched_approval = self.env["dynamic.approval"]
        for approval in approvals:
            if approval.is_matched_approval(res=res):
                matched_approval |= approval
        return matched_approval

    self_approval = fields.Boolean()
    line_manager_approval = fields.Boolean()
    employee_field = fields.Char()
