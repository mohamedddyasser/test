# -*- coding: utf-8 -*-
import logging
import ast
import urllib.parse
from datetime import datetime

from lxml import etree
from odoo import _, fields, models, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import frozendict

_logger = logging.getLogger(__name__)


class DynamicApprovalMixin(models.AbstractModel):
    _name = "dynamic.approval.mixin"
    _description = "Advanced Approval Mixin"
    _state_field = "state"  # to update field with status, you need to override in your module to add selection_add
    _state_from = [
        "draft"
    ]  # to check that this stage is source that need to convert from it
    _state_to = ["approved"]  # to convert to it when no pending approval
    _cancel_state = "cancel"
    _tier_validation_buttons_xpath = "/form/header/button[last()]"
    _tier_validation_manual_config = False
    _company_field = False  # to search for matched advanced approval based on company
    _not_matched_action_xml_id = False  # if no matched condition applied appear wizard to add custom action or restrict
    _reset_user = (
        "approve_requester_id"  # allow to appear request approve button to user
    )
    _custom_button_name = "Request Validation"

    dynamic_approve_request_ids = fields.One2many(
        comodel_name="dynamic.approval.request",
        inverse_name="res_id",
        auto_join=True,
        copy=False,
        domain=lambda self: [("res_model", "=", self._name)],
    )
    dynamic_approve_pending_group = fields.Boolean(
        compute="_compute_dynamic_approve_pending_group",
    )
    approve_requester_id = fields.Many2one(
        comodel_name="res.users",
        string="Approve Requester",
        copy=False,
    )
    dynamic_approval_id = fields.Many2one(
        comodel_name="dynamic.approval",
        string="Dynamic Approval",
        copy=False,
    )
    apply_recall = fields.Boolean(related="dynamic_approval_id.apply_recall")

    is_dynamic_approval_requester = fields.Boolean(
        compute="compute_is_dynamic_approval_requester"
    )
    state_from_name = fields.Char(
        copy=False,
        readonly=True,
    )
    validated = fields.Boolean(
        compute="_compute_validated_rejected", search="_search_validated"
    )
    need_validation = fields.Boolean(compute="_compute_need_validation")
    rejected = fields.Boolean(
        compute="_compute_validated_rejected", search="_search_rejected"
    )
    next_review = fields.Char(compute="_compute_next_review")
    approval_type = fields.Selection(
        string="Work Flow Type",
        selection=[
            ("auto", "Auto Select"),
            ("manual", "Manual Select"),
        ],
        default="auto",
        copy=False,
    )

    alias_id = fields.Many2one(
        "mail.alias",
        string="Email Alias",
        help=" Route Approval/Rejection Emails",
        compute="_compute_approval_alias",
        search="_search_approval_alias",
    )
    alias_domain = fields.Char("Alias domain", compute="_compute_alias_domain")
    alias_name = fields.Char(
        "Alias Name", copy=False, related="alias_id.alias_name", readonly=False
    )
    hr_officer = fields.Many2one(
        string="Hr Officer",
        comodel_name="res.users",
        compute="get_hr_approval_officer",
        readonly=True,
    )

    def get_hr_approval_officer(self):
        for rec in self:
            rec.hr_officer = False
            if rec.dynamic_approval_id:
                hr_officer = (
                    rec.dynamic_approval_id.approval_level_ids.filtered(
                        lambda x: x.hr_officer == True
                    ).user_id.id
                    or False
                )
                rec.hr_officer = hr_officer

    def _default_alias_domain(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mail.approvals.amail.domain")
        )

    def _compute_approval_alias(self):
        alias_id = (
            self.env["mail.alias"]
            .sudo()
            .search(
                [
                    ("alias_model_id.model", "=", self._name),
                    ("apply_dynamic_approval", "=", True),
                ],
                limit=1,
            )
        )
        if not alias_id.alias_name:
            approvals_alias = (
                self.env["ir.config_parameter"].sudo().get_param("mail.approvals.amail")
            )
            alias_id.alias_name = approvals_alias

        for record in self:
            record.alias_id = alias_id.id and alias_id

    def _search_approval_alias(self, operator, value):
        records = self.search([])  # Replace this with your own conditions
        ids = []
        for record in records:
            if operator == "=":
                if record.approval_alias == value:
                    ids.append(record.id)
            elif operator == "like":
                if value in record.approval_alias:
                    ids.append(record.id)
            # You can extend with more operators as per your requirements
        return [("id", "in", ids)]

    def _compute_alias_domain(self):
        alias_domain = self._default_alias_domain()
        for record in self:
            record.alias_domain = alias_domain

    def _compute_alias_dest(self):
        approvals_alias = (
            self.env["ir.config_parameter"].sudo().get_param("mail.approvals.amail")
        )
        approvals_domain = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mail.approvals.amail.domain")
        )

        if not (approvals_alias and approvals_domain):
            raise ValidationError(
                _(
                    "Can't route the approval email please configure the approval alias and domain"
                )
            )

        return approvals_alias + "@" + approvals_domain

    def _prepare_document_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        url = "{}/web#model={}&id={}&view_type=form".format(
            base_url, self._name, self.id
        )
        return url

    def get_approval_url(self, user=None, action=None):
        alias_email = self._compute_alias_dest()
        link = urllib.parse.quote(self._prepare_document_url())
        url = (
            "mailto:{}?subject=Re: {}&body= *********** please don't update the email content"
            " *********** \n This email is to {} the request with sequence {} \n ID:[{}] \n Object:[{}] \n ConfirmedBy:[{}] \n  [[NOTE]] \n "
            "[[ENDNOTE]] \n {} \n"
            "[[end]] \n".format(
                alias_email,
                self.name,
                action,
                self.name,
                self.id,
                self._name,
                user,
                link,
            )
        )
        return url

    # helper functions
    def _compute_next_review(self):
        for rec in self:
            review = rec.dynamic_approve_request_ids.sorted("sequence").filtered(
                lambda l: l.status == "pending"
            )[:1]
            rec.next_review = review and _("Next: %s") % review.display_name or ""

    def _compute_validated_rejected(self):
        for rec in self:
            rec.validated = self._calc_reviews_validated(
                rec.dynamic_approve_request_ids
            )
            rec.rejected = self._calc_reviews_rejected(rec.dynamic_approve_request_ids)

    @api.model
    def _calc_reviews_validated(self, reviews):
        """Override for different validation policy."""
        if not reviews:
            return False
        return not any([s != "approved" for s in reviews.mapped("status")])

    @api.model
    def _calc_reviews_rejected(self, reviews):
        """Override for different rejection policy."""
        return any([s == "rejected" for s in reviews.mapped("status")])

    @api.model
    def _search_validated(self, operator, value):
        assert operator in ("=", "!="), "Invalid domain operator"
        assert value in (True, False), "Invalid domain value"
        pos = self.search([(self._state_field, "in", self._state_from)]).filtered(
            lambda r: r.validated
        )
        if value:
            return [("id", "in", pos.ids)]
        else:
            return [("id", "not in", pos.ids)]

    def _compute_need_validation(self):
        for rec in self:
            if isinstance(rec.id, models.NewId):
                rec.need_validation = False
                continue
            tiers = self.env["dynamic.approval"].search(
                [
                    ("model", "=", self._name),
                    ("approval_level_ids", "!=", False),
                ]
            )
            valid_tiers = any([tier.is_matched_approval(rec) for tier in tiers])
            rec.need_validation = (
                not rec.dynamic_approve_request_ids
                and valid_tiers
                and getattr(rec, self._state_field) in self._state_from
            )

    @api.model
    def _search_rejected(self, operator, value):
        assert operator in ("=", "!="), "Invalid domain operator"
        assert value in (True, False), "Invalid domain value"
        pos = self.search([(self._state_field, "in", self._state_from)]).filtered(
            lambda r: r.rejected
        )
        if value:
            return [("id", "in", pos.ids)]
        else:
            return [("id", "not in", pos.ids)]

    def compute_is_dynamic_approval_requester(self):
        """return true if current user is who submit approval"""
        current_user = self.env.user
        for record in self:
            is_dynamic_approval_requester = False
            if (
                record.approve_requester_id
                and current_user == record.approve_requester_id
            ):
                is_dynamic_approval_requester = True
            elif not record.dynamic_approve_request_ids:
                is_dynamic_approval_requester = True
            elif getattr(record, self._reset_user) == current_user:
                is_dynamic_approval_requester = True
            elif self.env.user.has_group(
                "base_dynamic_approval.dynamic_approval_user_group"
            ):
                is_dynamic_approval_requester = True
            record.is_dynamic_approval_requester = is_dynamic_approval_requester

    def _compute_dynamic_approve_pending_group(self):
        for record in self:
            dynamic_approve_pending_group = False
            pend_approve_requests = record.dynamic_approve_request_ids
            skip_order_approval = any(
                pend_approve_requests.mapped("dynamic_approval_id").mapped(
                    "skip_order_approval"
                )
            )

            # Filter pending approval requests
            if not skip_order_approval:
                pend_approve_requests = pend_approve_requests.filtered(
                    lambda approver: approver.status == "pending"
                )

            # Find pending approval requests for the current user
            current_user_request = pend_approve_requests.filtered(
                lambda approver: approver.user_id.id == self.env.user.id
            )

            # Check if the current user has already approved
            user_has_already_approved = record.dynamic_approve_request_ids.filtered(
                lambda approver: approver.user_id.id == self.env.user.id
                and approver.status == "approved"
            )

            # Button visibility logic
            if current_user_request and not user_has_already_approved:
                if self.env.user.has_group(
                    "base_dynamic_approval.group_force_dynamic_approval"
                ):
                    dynamic_approve_pending_group = True
                else:
                    if self.env.user in current_user_request.get_approve_user():
                        dynamic_approve_pending_group = True

            # Set the computed field
            record.dynamic_approve_pending_group = dynamic_approve_pending_group

    def _notify_next_approval_request(self, matched_approval, user):
        """notify next approval"""
        self.ensure_one()
        if matched_approval.need_create_activity_to_approve:
            activity_type = self.env.ref(
                "base_dynamic_approval.mail_activity_type_waiting_approval",
                raise_if_not_found=False,
            )
            summary = _("Approval needed for %s", self.display_name)
            self._create_activity(user, summary, activity_type)
        if matched_approval.email_template_to_approve_id and user != self.env.user:
            email_values = {
                "email_to": user.email_formatted,
                "email_from": self.env.user.email_formatted,
            }
            self.dynamic_approval_id.email_template_to_approve_id.with_context(
                name_to=user.name, user_lang=user.lang, user_id=user.id
            ).send_mail(self.id, email_values=email_values, force_send=True)

    def _create_activity(self, users, summary, activity_type=False):
        """create activity based on next user"""
        if not activity_type:
            activity_type = self.env.ref(
                "mail.mail_activity_data_todo", raise_if_not_found=False
            )
        if activity_type:
            for record in self:
                for user in users:
                    try:
                        record.with_context(
                            mail_activity_quick_update=True
                        ).activity_schedule(
                            activity_type_id=activity_type.id,
                            summary=summary,
                            user_id=user.id,
                        )
                    except Exception as error_message:
                        _logger.exception(
                            "Cannot create activity for user %s. error: %s"
                            % (user.name or "", error_message)
                        )

    def _run_final_approve_function(self):
        """this method should be override to add custom function based on model"""
        return True

    def _action_final_approve(self):
        """mark order as approved"""
        self.ensure_one()
        self._run_final_approve_function()
        # self.write({
        #     self._state_field: self._state_to,
        # })
        # create activity based on setting
        if (
            self.dynamic_approval_id
            and self.dynamic_approval_id.default_notify_user_field_after_final_approve_id
        ):
            summary = _("Approval done for %s", self.display_name)
            user = getattr(
                self,
                self.dynamic_approval_id.default_notify_user_field_after_final_approve_id.name,
            )
            self._create_activity(user, summary)
        # send email to users
        if (
            self.dynamic_approval_id
            and self.dynamic_approval_id.notify_user_field_after_final_approve_ids
            and self.dynamic_approval_id.email_template_after_final_approve_id
        ):
            users_to_send = self.env["res.users"]
            for user_field in self.dynamic_approval_id.notify_user_field_rejection_ids:
                users_to_send |= getattr(self, user_field.name)
            # not send email for same user twice
            users_to_send = self.env["res.users"].browse(users_to_send.mapped("id"))
            for user in users_to_send:
                if user != self.env.user and user.email:
                    email_values = {
                        "email_to": user.email_formatted,
                        "email_from": self.env.user.email_formatted,
                    }
                    self.dynamic_approval_id.email_template_after_final_approve_id.with_context(
                        name_to=user.name, user_lang=user.lang, user_id=user.id
                    ).send_mail(
                        self.id, email_values=email_values, force_send=True
                    )
        if (
            self.dynamic_approval_id
            and self.dynamic_approval_id.after_final_approve_server_action_id
        ):
            action = self.dynamic_approval_id.after_final_approve_server_action_id.with_context(
                active_model=self._name,
                active_ids=[self.id],
                active_id=self.id,
                force_dynamic_validation=True,
            )
            try:
                action.run()
            except UserError as e:
                raise UserError(
                    f"Approval Rejection: record <{self.id}> model <{self._name}> encountered server action issue {str(e)}"
                )
            except ValidationError as e:
                raise ValidationError(
                    f"Approval Rejection: record <{self.id}> model <{self._name}> encountered server action issue {str(e)}"
                )
            except Exception as e:
                _logger.warning(
                    "Approval Rejection: record <%s> model <%s> encountered server action issue %s",
                    self.id,
                    self._name,
                    str(e),
                    exc_info=True,
                )

    def _get_user_approval_activities(self, users=False):
        """return users activities that need to mark done or cancel"""
        domain = [
            ("res_model", "=", self._name),
            ("res_id", "in", self.ids),
            "|",
            (
                "activity_type_id",
                "=",
                self.env.ref(
                    "base_dynamic_approval.mail_activity_type_waiting_approval"
                ).id,
            ),
            ("activity_type_id", "=", self.env.ref("mail.mail_activity_data_todo").id),
        ]
        if users:
            domain += [("user_id", "in", users.ids)]
        return self.env["mail.activity"].sudo().search(domain)

    def unlink(self):
        """remove approval requests when delete so"""
        self.remove_approval_requests()
        return super(DynamicApprovalMixin, self).unlink()

    def remove_approval_requests(self):
        """remove approval requests"""
        self.mapped("dynamic_approve_request_ids").sudo().unlink()

    def _get_pending_approvals(self, user):
        """return list of approval requests that need to approve"""
        self.ensure_one()
        pending_approval_ids = []
        for request in self.dynamic_approve_request_ids.filtered(
            lambda request_approve: request_approve.status in ["pending", "new"]
        ):
            if user in request.get_approve_user():
                pending_approval_ids.append(request.id)
            else:
                break
        return pending_approval_ids

    def _action_reset_original_state(self, reason="", reset_type="reject"):
        """
        set record to original state and notify user or approvers
        :param reason: reason for reset
        :param reset_type: reject / recall
        :param notify_approver: notify users who approved before
        """
        for record in self:
            pending_approve_requests = record.dynamic_approve_request_ids.filtered(
                lambda approver: approver.status == "pending"
            )
            approved_requests = record.dynamic_approve_request_ids.filtered(
                lambda approver: approver.status == "approved"
            )
            activity = record._get_user_approval_activities()
            if reset_type == "reject":
                if activity:
                    activity.action_feedback(feedback=_("Rejected, Reason ") + reason)
                else:
                    record.message_post(body=_("Rejected, Reason ") + reason)
                #  update approval request status
                pending_approve_requests.write(
                    {
                        "status": "rejected",
                        "approve_date": False,
                        "approved_by": False,
                        "reject_reason": reason,
                        "reject_date": datetime.now(),
                    }
                )

                # if pending_approve_requests.status == 'rejected':
                #     val = {'user_id': self.env.uid,
                #            'status': 'reject',
                #            'action_date': datetime.now(),
                #            'sale_id': self.id,
                #            'sale_order_status': self.state,
                #            }
                #     self.approval_history_ids.create(val)
                # create activity for user based on approval configuration
                if (
                    record.dynamic_approval_id
                    and record.dynamic_approval_id.default_notify_user_field_rejection_id
                ):
                    activity_user = getattr(
                        record,
                        record.dynamic_approval_id.default_notify_user_field_rejection_id.name,
                    )
                    if activity_user != self.env.user:
                        summary = _("%s approval request rejected", record.display_name)
                        record._create_activity(activity_user, summary)
                # send email template to users that need to know if record is rejected
                if (
                    record.dynamic_approval_id
                    and record.dynamic_approval_id.notify_user_field_rejection_ids
                    and record.dynamic_approval_id.rejection_email_template_id
                ):
                    users_to_send = self.env["res.users"]
                    for (
                        user_field
                    ) in record.dynamic_approval_id.notify_user_field_rejection_ids:
                        users_to_send |= getattr(record, user_field.name)
                    # not send email for same user twice
                    users_to_send = self.env["res.users"].browse(
                        users_to_send.mapped("id")
                    )
                    for user in users_to_send:
                        if user != self.env.user and user.email:
                            email_values = {
                                "email_to": user.email_formatted,
                                "email_from": self.env.user.email_formatted,
                            }
                            record.dynamic_approval_id.rejection_email_template_id.with_context(
                                name_to=user.name,
                                user_lang=user.lang,
                                reject_reason=reason,
                                user_id=user.id,
                            ).send_mail(
                                record.id, email_values=email_values, force_send=True
                            )
                # send email template to users who approved to record before about rejection
                if (
                    record.dynamic_approval_id
                    and record.dynamic_approval_id.need_notify_rejection_approved_user
                    and record.dynamic_approval_id.rejection_email_template_id
                ):
                    approved_users = approved_requests.mapped("approved_by")
                    for approved_user in approved_users:
                        if approved_user != self.env.user and approved_user.email:
                            email_values = {
                                "email_to": approved_user.email_formatted,
                                "email_from": self.env.user.email_formatted,
                            }
                            record.dynamic_approval_id.rejection_email_template_id.with_context(
                                name_to=approved_user.name,
                                user_lang=user.lang,
                                reject_reason=reason,
                                user_id=user.id,
                            ).send_mail(
                                record.id, email_values=email_values, force_send=True
                            )
                # run server action
                if (
                    record.dynamic_approval_id
                    and record.dynamic_approval_id.rejection_server_action_id
                ):
                    action = self.dynamic_approval_id.rejection_server_action_id.with_context(
                        active_model=self._name,
                        active_ids=[record.id],
                        active_id=record.id,
                        force_dynamic_validation=True,
                    )
                    try:
                        action.run()
                    except ValidationError as e:
                        raise ValidationError(
                            f"Approval Rejection: record <{self.id}> model <{self._name}> encountered server action issue {str(e)}"
                        )
                    except Exception as e:
                        _logger.warning(
                            "Approval Rejection: record <%s> model <%s> encountered server action issue %s",
                            self.id,
                            self._name,
                            str(e),
                            exc_info=True,
                        )

                    except Exception as e:
                        _logger.warning(
                            "Approval Rejection: record <%s> model <%s> encountered server action issue %s",
                            record.id,
                            record._name,
                            str(e),
                            exc_info=True,
                        )

            if reset_type == "recall":
                if activity:
                    activity.unlink()
                record.remove_approval_requests()
                # pending_approve_requests.write({'status': 'recall'})
                # approved_requests.write({'status': 'recall'})
                record.message_post(body=_("Recalled, Reason ") + reason)

                # if pending_approve_requests.status == 'recall':
                #     val = {'user_id': self.env.uid,
                #            'status': 'recall',
                #            'action_date': datetime.now(),
                #            'sale_id': self.id,
                #            'sale_order_status': self.state,
                #            }
                #     self.approval_history_ids.create(val)

                # create activity for user based on approval configuration
                if (
                    record.dynamic_approval_id
                    and record.dynamic_approval_id.default_notify_user_field_recall_id
                ):
                    activity_user = getattr(
                        record,
                        record.dynamic_approval_id.default_notify_user_field_recall_id.name,
                    )
                    if activity_user != self.env.user:
                        summary = _("%s approval request recalled", record.display_name)
                        record._create_activity(activity_user, summary)
                # send email template to users that need to know if record is recalled
                if (
                    record.dynamic_approval_id
                    and record.dynamic_approval_id.notify_user_field_recall_ids
                    and record.dynamic_approval_id.recall_email_template_id
                ):
                    users_to_send = self.env["res.users"]
                    for (
                        user_field
                    ) in record.dynamic_approval_id.notify_user_field_recall_ids:
                        users_to_send |= getattr(record, user_field.name)
                    # not send email for same user twice
                    users_to_send = self.env["res.users"].browse(
                        users_to_send.mapped("id")
                    )
                    for user in users_to_send:
                        if user != self.env.user and user.email:
                            email_values = {
                                "email_to": user.email_formatted,
                                "email_from": self.env.user.email_formatted,
                            }
                            record.dynamic_approval_id.recall_email_template_id.with_context(
                                name_to=user.name,
                                user_lang=user.lang,
                                recall_reason=reason,
                                user_id=user.id,
                            ).send_mail(
                                record.id, email_values=email_values, force_send=True
                            )
                # send email template to users who approved to record before about recall
                if (
                    record.dynamic_approval_id
                    and record.dynamic_approval_id.need_notify_recall_approved_user
                    and record.dynamic_approval_id.recall_email_template_id
                ):
                    approved_users = approved_requests.mapped("approved_by")
                    for approved_user in approved_users:
                        if approved_user != self.env.user and approved_user.email:
                            email_values = {
                                "email_to": approved_user.email_formatted,
                                "email_from": self.env.user.email_formatted,
                            }
                            record.dynamic_approval_id.recall_email_template_id.with_context(
                                name_to=approved_user.name,
                                user_lang=user.lang,
                                recall_reason=reason,
                                user_id=user.id,
                            ).send_mail(
                                record.id, email_values=email_values, force_send=True
                            )

                # run server action
                if (
                    record.dynamic_approval_id
                    and record.dynamic_approval_id.recall_server_action_id
                ):
                    action = (
                        self.dynamic_approval_id.recall_server_action_id.with_context(
                            active_model=self._name,
                            active_ids=[record.id],
                            active_id=record.id,
                            force_dynamic_validation=True,
                        )
                    )
                    try:
                        action.run()
                    except ValidationError as e:
                        raise ValidationError(
                            f"Approval Rejection: record <{self.id}> model <{self._name}> encountered server action issue {str(e)}"
                        )
                    except Exception as e:
                        _logger.warning(
                            "Approval Rejection: record <%s> model <%s> encountered server action issue %s",
                            self.id,
                            self._name,
                            str(e),
                            exc_info=True,
                        )

                    except Exception as e:
                        _logger.warning(
                            "Approval Recall: record <%s> model <%s> encountered server action issue %s",
                            record.id,
                            record._name,
                            str(e),
                            exc_info=True,
                        )

            # record.write({
            #     record._state_field: record.state_from_name or record._state_from[0]
            # })

    def is_transfer_from_to_status(self, vals):
        self.ensure_one()
        return (
            getattr(self, self._state_field) in self._state_from
            and vals.get(self._state_field) in self._state_to
        )

    @api.model
    def _get_under_validation_exceptions(self):
        """Extend for more field exceptions."""
        return [
            "message_follower_ids",
            "access_token",
            "release_to_pay_manual",
            "message_main_attachment_id",
        ]

    @api.model
    def _get_after_validation_exceptions(self):
        """Extend for more field exceptions."""
        return [
            "message_follower_ids",
            "access_token",
            "managerapp_date",
            "approve_manager_id",
            "userrapp_date",
            "approve_employee_id",
            "employee_confirm_id",
            "confirm_date",
            "release_to_pay_manual",
            "message_main_attachment_id",
        ]

    def _check_allow_write_under_validation(self, vals):
        """Allow to add exceptions for fields that are allowed to be written
        even when the record is under validation."""
        exceptions = self._get_under_validation_exceptions()
        for val in vals:
            if val not in exceptions:
                print(val)
                _logger.warning(val)
                return False
        return True

    def _check_allow_write_after_validation(self, vals):
        """Allow to add exceptions for fields that are allowed to be written
        even when the record is under validation."""
        exceptions = self._get_after_validation_exceptions()
        for val in vals:
            if val not in exceptions:
                print("_check_allow_write_after_validation")
                print(val)
                _logger.warning(val)
                return False
        return True

    # actions workflow

    def action_dynamic_approval_request(self):
        """
        search for advanced approvals that match current record and add approvals
        if record does not match then appear wizard to confirm order without approval
        """
        # for record in self:
        #     if record.approval_type == 'auto':
        #         matched_approval = self.env['dynamic.approval'].action_set_approver(
        #             model=self._name,
        #             res=record,
        #         )
        #         record.apply_dynamic_approval(matched_approval)

        print(self._name)
        approval_id = (
            self.env["dynamic.approval"]
            .sudo()
            .search(
                [
                    ("model_id.model", "=", "material.purchase.requisition"),
                    ("active", "=", True),
                ]
            )
        )
        print(approval_id)
        active_rec = self
        # approval_id = self.env['dynamic.approval'].search([('dynamic_approve', '=', True)])
        if approval_id and self.env.user.has_group(
            "base_dynamic_approval.dynamic_approval_admin_group"
        ):
            return {
                "type": "ir.actions.act_window",
                "name": "Define Approval Levels",
                "res_model": "levels.dynamic.approval.wizard",
                "view_mode": "form",
                "view_id": self.env.ref(
                    "base_dynamic_approval.levels_dynamic_approval_wizard_form"
                ).id,
                "target": "new",
            }
        else:
            for record in self:
                company = (
                    getattr(record, self._company_field)
                    if self._company_field
                    else False
                )
                if getattr(record, record._state_field) in self._state_from:
                    if record.dynamic_approve_request_ids:
                        record.remove_approval_requests()
                        # mark any old activity as done to allow create new activity
                        activity = record._get_user_approval_activities()
                        if activity:
                            activity.action_feedback()
                    if record.approval_type == "auto":
                        manager = None
                        if (
                            approval_id.line_manager_approval
                            and not self.env.user.has_group(
                                "hr_exit_process.group_department_manager_for_exit"
                            )
                        ):
                            manager = (
                                self.env["hr.employee"]
                                .search([("user_id", "=", active_rec.create_uid.id)])
                                .parent_id.user_id
                            )
                        matched_approval = self.env[
                            "dynamic.approval"
                        ].action_set_approver(
                            model=self._name,
                            res=record,
                            company=company,
                            manager=manager,
                        )
                        record.apply_dynamic_approval(matched_approval)
                    else:
                        view_id = self.env.ref(
                            "base_dynamic_approval.work_flow_select_form"
                        )
                        return {
                            "name": _("Work Flow Selection"),
                            "type": "ir.actions.act_window",
                            "res_model": "work.flow.select",
                            "view_mode": "form",
                            "view_id": view_id.id,
                            "target": "new",
                            "context": {
                                "default_res_model": record._name,
                                "default_res_id": record.id,
                            },
                        }
                else:
                    raise UserError(_("This status is not allowed to request approval"))
        if self._name == "account.batch.payment" and self.state == "under_approval":
            self.under_approval_check = True

    def apply_dynamic_approval(self, matched_approval):
        if matched_approval:
            vals = {
                "approve_requester_id": self.env.user.id,
                "dynamic_approval_id": matched_approval.id,
                "state_from_name": getattr(self, self._state_field),
            }
            if matched_approval.state_under_approval:
                vals.update({"state": matched_approval.state_under_approval})
            self.with_context(force_dynamic_validation=True).write(vals)
            next_waiting_approval = self.dynamic_approve_request_ids.sorted(
                lambda x: (x.sequence, x.id)
            )[0]
            next_waiting_approval.status = "pending"
            if next_waiting_approval.get_approve_user():
                user = next_waiting_approval.get_approve_user()[0]
                self._notify_next_approval_request(matched_approval, user)

            # if next_waiting_approval and self.approve_requester_id:
            #     val = {'user_id': self.env.uid,
            #            'status': 'request_approval',
            #            'action_date': datetime.now(),
            #            'sale_id': self.id,
            #            'sale_order_status': self.state,
            #            }
            #     self.approval_history_ids.create(val)
        else:
            if self._not_matched_action_xml_id:
                action_id = self._not_matched_action_xml_id
                action = self.env["ir.actions.act_window"]._for_xml_id(action_id)
                return action

    def action_under_approval(self, note="", signature=False, stamp=False):
        """
        Change status of approval request to approved and trigger next approval level or change status to be approved.
        :param note: Approval notes that the user will add and store in approval requests and add as activity feedback.
        """
        for record in self:
            # Retrieve all approval requests for this record (not just for the current user)
            all_approve_requests = record.dynamic_approve_request_ids

            # Determine if we should skip the order approval process
            skip_order_approval = any(
                all_approve_requests.mapped("dynamic_approval_id").mapped(
                    "skip_order_approval"
                )
            )

            # Filter to get the pending approval requests for the current user
            current_user_request = all_approve_requests.filtered(
                lambda r: r.user_id.id == self.env.user.id
                and r.status in ("pending", "new")
            )

            # If the current user's request exists and is pending
            if current_user_request:
                # Approve the current user's request
                current_user_request.write(
                    {
                        "approve_date": datetime.now(),
                        "approved_by": self.env.user.id,
                        "status": "approved",
                        "approve_note": note,
                        "approve_signature": signature,
                    }
                )

                # If skip_order_approval is True, approve all prior requests (those with lower sequence)
                if skip_order_approval:
                    # Sort all approval requests by sequence
                    sorted_requests = all_approve_requests.sorted(lambda x: x.sequence)
                    current_request = sorted_requests.filtered(
                        lambda x: x.user_id.id == self.env.user.id
                    )

                    if current_request:
                        # Approve all requests with a lower sequence than the current user's request
                        prior_requests = sorted_requests.filtered(
                            lambda r: r.sequence < current_request[0].sequence
                            and r.status != "approved"
                        )
                        for prior_request in prior_requests:
                            prior_request.write(
                                {
                                    "approve_date": datetime.now(),
                                    "approved_by": self.env.user.id,
                                    "status": "approved",
                                }
                            )

            # Handle activity feedback
            activity = record._get_user_approval_activities()
            if activity:
                activity.action_feedback(feedback=note)
            else:
                msg = _("Approved")
                if note:
                    msg += " " + note
                record.message_post(body=msg)

            # Run server action if defined
            if record.dynamic_approval_id.to_approve_server_action_id:
                action = (
                    record.dynamic_approval_id.to_approve_server_action_id.with_context(
                        active_model=self._name,
                        active_ids=[record.id],
                        active_id=record.id,
                        force_dynamic_validation=True,
                    )
                )
                try:
                    action.run()
                except ValidationError as e:
                    raise ValidationError(
                        f"Approval Rejection: record <{self.id}> model <{self._name}> encountered server action issue {str(e)}"
                    )
                except UserError as e:
                    raise UserError(
                        f"Approval Rejection: record <{self.id}> model <{self._name}> encountered server action issue {str(e)}"
                    )
                except Exception as e:
                    _logger.warning(
                        "Approval Recall: record <%s> model <%s> encountered server action issue %s",
                        record.id,
                        record._name,
                        str(e),
                        exc_info=True,
                    )

            # Process next approval requests
            new_approve_requests = record.dynamic_approve_request_ids.filtered(
                lambda approver: approver.status == "new"
            )
            if new_approve_requests:
                next_waiting_approval = new_approve_requests.sorted(
                    lambda x: (x.sequence, x.id)
                )[0]
                next_waiting_approval.status = "pending"
                if next_waiting_approval.get_approve_user():
                    user = next_waiting_approval.get_approve_user()[0]
                    record._notify_next_approval_request(
                        record.dynamic_approval_id, user
                    )
            else:
                record._action_final_approve()

        return True

    def _check_previously_action(self):
        user = self.env.user
        approval_requests = self.dynamic_approve_request_ids.filtered(
            lambda req: (user == req.user_id or user in req.group_id.users)
            and req.status == "pending"
        )
        if approval_requests:
            return False
        return True

    # bhavesh
    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        res = super().get_view(view_id=view_id, view_type=view_type, **options)

        View = self.env["ir.ui.view"]

        # Override context for postprocessing
        if view_id and res.get("base_model", self._name) != self._name:
            View = View.with_context(base_model_name=res["base_model"])
        if view_type == "form" and not self._tier_validation_manual_config:
            doc = etree.XML(res["arch"])
            params = {
                "model": self._name,
                "state_field": self._state_field,
                "state_from": ",".join("'%s'" % state for state in self._state_from),
                "custom_button_name": self._custom_button_name,
            }
            all_models = res["models"].copy()
            for node in doc.xpath(self._tier_validation_buttons_xpath):
                # By default, after the last button of the header
                str_element = self.env["ir.qweb"]._render(
                    "base_dynamic_approval.tier_validation_buttons", params
                )
                new_node = etree.fromstring(str_element)
                new_arch, new_models = View.postprocess_and_fields(new_node, self._name)
                new_node = etree.fromstring(new_arch)
                for new_element in new_node:
                    node.addnext(new_element)
            if len(doc.xpath("/form/sheet/notebook")) > 0:
                for node in doc.xpath("/form/sheet/notebook"):
                    str_element = self.env["ir.qweb"]._render(
                        "base_dynamic_approval.approval_page", params
                    )
                    new_node = etree.fromstring(str_element)
                    new_arch, new_models = View.postprocess_and_fields(
                        new_node, self._name
                    )
                    # approval_type_template = self.env["ir.qweb"]._render("base_dynamic_approval.approval_type_template")
                    # node.append(etree.fromstring(approval_type_template))
                    for model in new_models:
                        if model in all_models:
                            continue
                        if model not in res["models"]:
                            all_models[model] = new_models[model]
                        else:
                            all_models[model] = res["models"][model]
                    new_node = etree.fromstring(new_arch)
                    node.append(new_node)
            else:
                for node in doc.xpath("/form/sheet"):
                    str_element = self.env["ir.qweb"]._render(
                        "base_dynamic_approval.approval_notebook", params
                    )
                    new_node = etree.fromstring(str_element)
                    new_arch, new_models = View.postprocess_and_fields(
                        new_node, self._name
                    )
                    # approval_type_template = self.env["ir.qweb"]._render("base_dynamic_approval.approval_type_template")
                    # node.append(etree.fromstring(approval_type_template))
                    for model in new_models:
                        if model in all_models:
                            continue
                        if model not in res["models"]:
                            all_models[model] = new_models[model]
                        else:
                            all_models[model] = res["models"][model]
                    new_node = etree.fromstring(new_arch)
                    node.append(new_node)
            for node in doc.xpath("/form/sheet"):
                str_element = self.env["ir.qweb"]._render(
                    "base_dynamic_approval.tier_validation_label", params
                )
                new_node = etree.fromstring(str_element)
                new_arch, new_models = View.postprocess_and_fields(new_node, self._name)
                new_node = etree.fromstring(new_arch)
                for new_element in new_node:
                    node.addprevious(new_element)
            res["arch"] = etree.tostring(doc)
            res["models"] = frozendict(all_models)
        return res

    # Priya
    # @api.model
    # def get_view(self, view_id=None, view_type="form", **options):
    #     res = super().get_view(view_id=view_id, view_type=view_type, **options)
    #
    #     View = self.env["ir.ui.view"]
    #
    #     # Override context for postprocessing
    #     if view_id and res.get("base_model", self._name) != self._name:
    #         View = View.with_context(base_model_name=res["base_model"])
    #     if view_type == "form" and not self._tier_validation_manual_config:
    #         doc = etree.XML(res["arch"])
    #         params = {
    #             "state_field": self._state_field,
    #             "state_from": ",".join("'%s'" % state for state in self._state_from),
    #         }
    #         all_models = res["models"].copy()
    #         for node in doc.xpath(self._tier_validation_buttons_xpath):
    #             # By default, after the last button of the header
    #             str_element = self.env["ir.qweb"]._render(
    #                 "base_dynamic_approval.tier_validation_buttons", params
    #             )
    #             new_node = etree.fromstring(str_element)
    #             new_arch, new_models = View.postprocess_and_fields(new_node, self._name)
    #             new_node = etree.fromstring(new_arch)
    #             for new_element in new_node:
    #                 node.addnext(new_element)
    #         for node in doc.xpath("/form/sheet"):
    #             str_element = self.env["ir.qweb"]._render(
    #                 "base_dynamic_approval.tier_validation_label", params
    #             )
    #             new_node = etree.fromstring(str_element)
    #             new_arch, new_models = View.postprocess_and_fields(new_node, self._name)
    #             new_node = etree.fromstring(new_arch)
    #             for new_element in new_node:
    #                 node.addprevious(new_element)
    #             str_element = self.env["ir.qweb"]._render(
    #                 "base_dynamic_approval.approval_tree", params
    #             )
    #             new_node = etree.fromstring(str_element)
    #             new_arch, new_models = View.postprocess_and_fields(new_node, self._name)
    #             for model in new_models:
    #                 if model in all_models:
    #                     continue
    #                 if model not in res["models"]:
    #                     all_models[model] = new_models[model]
    #                 else:
    #                     all_models[model] = res["models"][model]
    #             new_node = etree.fromstring(new_arch)
    #             node.append(new_node)
    #         res["arch"] = etree.tostring(doc)
    #         res["models"] = frozendict(all_models)
    #     return res

    # BK Comment
    # @api.model
    # def get_view(
    #         self, view_id=None, view_type="form", **options
    # ):
    #     res = super().get_view(
    #         view_id=view_id, view_type=view_type, **options
    #     )
    #     if view_type == "form" and not self._tier_validation_manual_config:
    #         doc = etree.XML(res["arch"])
    #         params = {
    #             "state_field": self._state_field,
    #             "state_from": ",".join("'%s'" % state for state in self._state_from),
    #         }
    #         for node in doc.xpath(self._tier_validation_buttons_xpath):
    #             # By default, after the last button of the header
    #             str_element = self.env["ir.qweb"]._render(
    #                 "base_dynamic_approval.tier_validation_buttons", params
    #             )
    #             new_node = etree.fromstring(str_element)
    #             for new_element in new_node:
    #                 node.addnext(new_element)
    #         for node in doc.xpath("/form/sheet"):
    #             str_element = self.env["ir.qweb"]._render(
    #                 "base_dynamic_approval.tier_validation_label", params
    #             )
    #             new_node = etree.fromstring(str_element)
    #             approval_type_template = self.env["ir.qweb"]._render("base_dynamic_approval.approval_type_template")
    #             node.append(etree.fromstring(approval_type_template))
    #             for new_element in new_node:
    #                 node.addprevious(new_element)
    #             str_element = self.env["ir.qweb"]._render("base_dynamic_approval.approval_tree")
    #             node.append(etree.fromstring(str_element))
    #         View = self.env["ir.ui.view"]
    #
    #         # Override context for postprocessing
    #         if view_id and res.get("base_model", self._name) != self._name:
    #             View = View.with_context(base_model_name=res["base_model"])
    #         new_arch, new_fields = View.postprocess_and_fields(doc, self._name)
    #         print(new_arch)
    #         print(new_fields)
    #         res["arch"] = new_arch
    #         # We don't want to loose previous configuration, so, we only want to add
    #         # the new fields
    #         # new_fields.update(res["fields"])
    #         res["models"] = new_fields
    #     return res
    def write(self, vals):
        force_dynamic_validation = self.env.context.get(
            "force_dynamic_validation", False
        )
        if not force_dynamic_validation:
            for rec in self:
                rec._check_changes_validity(vals)
            if vals.get(self._state_field) in (self._state_from + [self._cancel_state]):
                self.mapped("dynamic_approve_request_ids").unlink()
        self.check_context_vals(vals)
        return super(DynamicApprovalMixin, self).write(vals)

    def _check_changes_validity(self, vals):
        # TODO: Before Approval Checks
        if not self.dynamic_approve_request_ids:
            if self.need_validation:
                if vals.get(self._state_field):
                    if self.is_transfer_from_to_status(vals):
                        raise ValidationError("This Document Need Approval !")
        # TODO: Under Approval Checks
        elif self.dynamic_approve_request_ids and not self.validated:
            if not self._check_allow_write_under_validation(vals):
                raise ValidationError(_("The operation is under validation."))
        # TODO: After Approval Checks
        elif self.dynamic_approve_request_ids and self.validated:
            if vals.get(self._state_field):
                new_vals = vals.copy()
                del new_vals[self._state_field]
                # if not self._check_allow_write_after_validation(new_vals):
                #     raise ValidationError(_("The operation is not allowed because this document is fully approved !"))
            else:
                if (
                    not self._check_allow_write_after_validation(vals)
                    and "applicant_name_id" not in vals
                ):
                    raise ValidationError(
                        _(
                            "The operation is not allowed because this document is fully approved !"
                        )
                    )

    def check_context_vals(self, vals):
        to_remove_value = self.env.context.get("to_remove_value")
        if to_remove_value:
            if vals.get(to_remove_value):
                del vals[to_remove_value]

    show_original_buttons = fields.Boolean(compute="_show_original_buttons")

    @api.model
    def get_dynamic_approval(self):
        d = self.env["dynamic.approval"].search([("model_id", "=", self._name)])
        return d[0] if d else []

    def _show_original_buttons(self):
        da = self.get_dynamic_approval()
        if da:
            d = da.approval_condition_ids.mapped("filter_domain")
            recs = self.search(ast.literal_eval(d[0])) if d else []
        for rec in self:
            if not da:
                rec.show_original_buttons = True
                continue
            if not d:
                rec.show_original_buttons = False
                continue
            rec.show_original_buttons = rec not in recs
