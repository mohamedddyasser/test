# -*- coding: utf-8 -*-
import ast
import email
import html
import logging
import re
from email.message import EmailMessage
from xmlrpc import client as xmlrpclib

from odoo import _, api, models, tools
from odoo.exceptions import MissingError, ValidationError

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _document_check_access_per_user(
        self, model_name, document_id, user_id, access_token=None
    ):
        document = self.env[model_name].browse([document_id])
        document_sudo = document.with_user(user_id).exists()
        if not document_sudo:
            raise MissingError(_("This document does not exist."))
        return document_sudo.with_user(user_id)

    def _submit_approval_action(self, alias_id, id, user, action, action_note=None):
        record_id = self._document_check_access_per_user(
            alias_id.alias_model_id.model, int(id), user
        )
        is_previously_done = record_id._check_previously_action()
        if is_previously_done:
            _logger.info("already processed before")
        else:
            if action == "approve":
                record_id.action_under_approval(note=action_note, signature=False)
            if action == "reject":
                record_id._action_reset_original_state(reason=action_note)

    @api.model
    def message_process(
        self,
        model,
        message,
        custom_values=None,
        save_original=False,
        strip_attachments=False,
        thread_id=None,
    ):
        """Process an incoming RFC2822 email message, relying on
         ``mail.message.parse()`` for the parsing operation,
         and ``message_route()`` to figure out the target model.

         Once the target model is known, its ``message_new`` method
         is called with the new message (if the thread record did not exist)
         or its ``message_update`` method (if it did).

        :param string model: the fallback model to use if the message
            does not match any of the currently configured mail aliases
            (may be None if a matching alias is supposed to be present)
        :param message: source of the RFC2822 message
        :type message: string or xmlrpclib.Binary
        :type dict custom_values: optional dictionary of field values
             to pass to ``message_new`` if a new record needs to be created.
             Ignored if the thread record already exists, and also if a
             matching mail.alias was found (aliases define their own defaults)
        :param bool save_original: whether to keep a copy of the original
             email source attached to the message after it is imported.
        :param bool strip_attachments: whether to strip all attachments
             before processing the message, in order to save some space.
        :param int thread_id: optional ID of the record/thread from ``model``
            to which this mail should be attached. When provided, this
            overrides the automatic detection based on the message
            headers.
        """
        # extract message bytes - we are forced to pass the message as binary because
        # we don't know its encoding until we parse its headers and hence can't
        # convert it to utf-8 for transport between the mailgate script and here.
        if isinstance(message, xmlrpclib.Binary):
            message = bytes(message.data)
        if isinstance(message, str):
            message = message.encode("utf-8")
        message = email.message_from_bytes(message, policy=email.policy.SMTP)

        # parse the message, verify we are not in a loop by checking message_id is not duplicated
        msg_dict = self.message_parse(message, save_original=save_original)

        body = msg_dict["body"]
        obj_id = False
        body_content = body.split("[[end]]")
        if body_content:
            strip_attachments = True

        if strip_attachments:
            msg_dict.pop("attachments", None)

        existing_msg_ids = self.env["mail.message"].search(
            [("message_id", "=", msg_dict["message_id"])], limit=1
        )
        if existing_msg_ids:
            _logger.info(
                "Ignored mail from %s to %s with Message-Id %s: found duplicated Message-Id during processing",
                msg_dict.get("email_from"),
                msg_dict.get("to"),
                msg_dict.get("message_id"),
            )
            return False

        # find possible routes for the message
        routes = self.message_route(message, msg_dict, model, thread_id, custom_values)
        thread_id = self._message_route_process(message, msg_dict, routes)
        return thread_id

    @api.model
    def message_route(
        self, message, message_dict, model=None, thread_id=None, custom_values=None
    ):
        """Overrides to include the reply emails for Dynamic approvals to be routed to the record related to the alias
        attached to the record.
        """
        if not isinstance(message, EmailMessage):
            raise TypeError(
                "message must be an email.message.EmailMessage at this point"
            )
        catchall_alias = (
            self.env["ir.config_parameter"].sudo().get_param("mail.catchall.alias")
        )
        bounce_alias = (
            self.env["ir.config_parameter"].sudo().get_param("mail.bounce.alias")
        )
        fallback_model = model

        # get email.message.Message variables for future processing
        message_id = message_dict["message_id"]

        # compute references to find if message is a reply to an existing thread
        thread_references = message_dict["references"] or message_dict["in_reply_to"]
        msg_references = [
            re.sub(r"[\r\n\t ]+", r"", ref)  # "Unfold" buggy references
            for ref in tools.mail_header_msgid_re.findall(thread_references)
            if "reply_to" not in ref
        ]
        mail_messages = (
            self.env["mail.message"]
            .sudo()
            .search(
                [("message_id", "in", msg_references)],
                limit=1,
                order="id desc, message_id",
            )
        )
        is_a_reply = bool(mail_messages)
        reply_model, reply_thread_id = mail_messages.model, mail_messages.res_id

        # author and recipients
        email_from = message_dict["email_from"]
        email_from_localpart = (
            (tools.email_split(email_from) or [""])[0].split("@", 1)[0].lower()
        )
        email_to = message_dict["to"]
        email_to_localparts = [
            e.split("@", 1)[0].lower() for e in (tools.email_split(email_to) or [""])
        ]
        # Delivered-To is a safe bet in most modern MTAs, but we have to fallback on To + Cc values
        # for all the odd MTAs out there, as there is no standard header for the envelope's `rcpt_to` value.
        rcpt_tos_localparts = [
            e.split("@")[0].lower()
            for e in tools.email_split(message_dict["recipients"])
        ]
        rcpt_tos_valid_localparts = [to for to in rcpt_tos_localparts]

        # 0. Handle bounce: verify whether this is a bounced email and use it to collect bounce data and update notifications for customers
        #    Bounce alias: if any To contains bounce_alias@domain
        #    Bounce message (not alias)
        #       See http://datatracker.ietf.org/doc/rfc3462/?include_text=1
        #        As all MTA does not respect this RFC (googlemail is one of them),
        #       we also need to verify if the message come from "mailer-daemon"
        #    If not a bounce: reset bounce information
        if bounce_alias and any(email == bounce_alias for email in email_to_localparts):
            self._routing_handle_bounce(message, message_dict)
            return []
        if (
            message.get_content_type() == "multipart/report"
            or email_from_localpart == "mailer-daemon"
        ):
            self._routing_handle_bounce(message, message_dict)
            return []
        self._routing_reset_bounce(message, message_dict)

        # 1. Handle reply
        #    if destination = alias with different model -> consider it is a forward and not a reply
        #    if destination = alias with same model -> check contact settings as they still apply
        if reply_model and reply_thread_id:
            reply_model_id = self.env["ir.model"]._get_id(reply_model)
            other_model_aliases = self.env["mail.alias"].search(
                [
                    "&",
                    "&",
                    ("alias_name", "!=", False),
                    ("alias_name", "in", email_to_localparts),
                    ("alias_model_id", "!=", reply_model_id),
                ]
            )
            if other_model_aliases:
                is_a_reply = False
                rcpt_tos_valid_localparts = [
                    to
                    for to in rcpt_tos_valid_localparts
                    if to in other_model_aliases.mapped("alias_name")
                ]

        if is_a_reply:
            reply_model_id = self.env["ir.model"]._get_id(reply_model)
            dest_aliases = self.env["mail.alias"].search(
                [
                    ("alias_name", "in", rcpt_tos_localparts),
                    ("alias_model_id", "=", reply_model_id),
                ],
                limit=1,
            )

            user_id = (
                self._mail_find_user_for_gateway(email_from, alias=dest_aliases).id
                or self._uid
            )
            route = self._routing_check_route(
                message,
                message_dict,
                (reply_model, reply_thread_id, custom_values, user_id, dest_aliases),
                raise_exception=False,
            )
            if route:
                _logger.info(
                    "Routing mail from %s to %s with Message-Id %s: direct reply to msg: model: %s, thread_id: %s, custom_values: %s, uid: %s",
                    email_from,
                    email_to,
                    message_id,
                    reply_model,
                    reply_thread_id,
                    custom_values,
                    self._uid,
                )
                return [route]
            elif route is False:
                return []

        # 2. Handle new incoming email by checking aliases and applying their settings
        if rcpt_tos_localparts:
            # no route found for a matching reference (or reply), so parent is invalid
            message_dict.pop("parent_id", None)

            # check it does not directly contact catchall
            if (
                catchall_alias
                and email_to_localparts
                and all(
                    email_localpart == catchall_alias
                    for email_localpart in email_to_localparts
                )
            ):
                _logger.info(
                    "Routing mail from %s to %s with Message-Id %s: direct write to catchall, bounce",
                    email_from,
                    email_to,
                    message_id,
                )
                body = self.env.ref("mail.mail_bounce_catchall")._render(
                    {
                        "message": message,
                    },
                    engine="ir.qweb",
                )
                self._routing_create_bounce_email(
                    email_from,
                    body,
                    message,
                    references=message_id,
                    reply_to=self.env.company.email,
                )
                return []
            dest_aliases = self.env["mail.alias"].search(
                [("alias_name", "in", rcpt_tos_valid_localparts)]
            )
            if dest_aliases:
                routes = []
                for alias in dest_aliases:
                    user_id = (
                        self._mail_find_user_for_gateway(email_from, alias=alias).id
                        or self._uid
                    )
                    force_thread_id = alias.alias_force_thread_id
                    if alias.apply_dynamic_approval:
                        try:
                            body = html.unescape(message_dict["body"])
                            obj_id = False
                            body_content = body.split("[[end]]")
                            if body_content:
                                body = body_content[0]
                                for i in body.split():
                                    if re.search(r"(?<=\[).+?(?=\])", i):
                                        id = i.split(":[")[1].split("]")[0]
                                        if id.isdigit():
                                            obj_id = int(id)
                                            force_thread_id = obj_id
                                            break
                                if not obj_id:
                                    raise ValidationError(
                                        _("Can't get value for object ID")
                                    )
                                action_note = ""
                                note_section = body.split("[[NOTE]]")
                                note_section = (
                                    note_section
                                    and len(note_section) > 1
                                    and note_section[1]
                                )
                                if note_section:
                                    end_note = re.sub("<.*?>", "", note_section).split(
                                        "[[ENDNOTE]]"
                                    )
                                    if end_note:
                                        action_note = end_note[0].replace("\n", "")
                                action = (
                                    body.find("approve") > 0 and "approve" or "reject"
                                )
                                self._submit_approval_action(
                                    alias, obj_id, user_id, action, action_note
                                )
                                message_dict["body"] = body

                            else:
                                raise ValidationError(_("Can't get email body"))

                        except Exception as e:
                            _logger.info(
                                "exception during processing approval email %s" % e
                            )
                            _logger.info(
                                "Can't apply the approval cycle for the message"
                                + str(html.unescape(message_dict["body"]))
                            )
                            return
                    route = (
                        alias.sudo().alias_model_id.model,
                        force_thread_id,
                        ast.literal_eval(alias.alias_defaults),
                        user_id,
                        alias,
                    )
                    route = self._routing_check_route(
                        message, message_dict, route, raise_exception=True
                    )
                    if route:
                        _logger.info(
                            "Routing mail from %s to %s with Message-Id %s: direct alias match: %r",
                            email_from,
                            email_to,
                            message_id,
                            route,
                        )
                        routes.append(route)
                return routes

        # 3. Fallback to the provided parameters, if they work
        if fallback_model:
            # no route found for a matching reference (or reply), so parent is invalid
            message_dict.pop("parent_id", None)
            user_id = self._mail_find_user_for_gateway(email_from).id or self._uid
            route = self._routing_check_route(
                message,
                message_dict,
                (fallback_model, thread_id, custom_values, user_id, None),
                raise_exception=True,
            )
            if route:
                _logger.info(
                    "Routing mail from %s to %s with Message-Id %s: fallback to model:%s, thread_id:%s, custom_values:%s, uid:%s",
                    email_from,
                    email_to,
                    message_id,
                    fallback_model,
                    thread_id,
                    custom_values,
                    user_id,
                )
                return [route]

        # ValueError if no routes found and if no bounce occurred
        raise ValueError(
            "No possible route found for incoming message from %s to %s (Message-Id %s:). "
            "Create an appropriate mail.alias or force the destination model."
            % (email_from, email_to, message_id)
        )
