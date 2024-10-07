# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, api
from num2words import num2words


class print_check(models.AbstractModel):
    _name = "report.dev_print_cheque.report_print_cheque"
    _description = "Print cheque From Account Payment"

    def get_date(self, date):
        if date:
            date = date.strftime("%Y-%m-%d")
            date = date.split("-")
            return date
        return ""

    def get_partner_name(self, obj, p_text):
        if p_text and obj.partner_text:
            if p_text == "prefix":
                return obj.partner_text + " " + obj.partner_id.name
            else:
                return obj.partner_id.name + " " + obj.partner_text

        return obj.partner_id.name

    def amount_word(self, obj):
        if obj.partner_id and obj.partner_id.lang:
            amt_word = obj.with_context(
                lang=obj.partner_id.lang
            ).currency_id.amount_to_text(obj.amount)
        else:
            amt_word = obj.currency_id.amount_to_text(obj.amount)

        # Add Only in the end of the amount to words label
        if amt_word:
            amt_word += " Only"

        lst = amt_word.split(" ")

        lst_len = len(lst)
        amt_word_list = []
        step = (
            (int(obj.cheque_formate_id.word_in_f_line) + 1)
            if obj.cheque_formate_id.word_in_f_line
            else lst_len - 1
        )
        for i in range(0, lst_len, step):
            sublist = lst[i : i + step]
            amt_word_list.append(" ".join(sublist))

        if obj.cheque_formate_id.is_star_word and amt_word_list:
            amt_word_list[0] = "***" + amt_word_list[0]
            amt_word_list[-1] = amt_word_list[-1] + "***"

        return amt_word_list

    def get_footer_text(self, footer_text, cheque_num):
        if footer_text and cheque_num:
            return str(footer_text) + " " + str(cheque_num)

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["account.payment"].browse(docids)
        return {
            "doc_ids": docs.ids,
            "doc_model": "account.payment",
            "docs": docs,
            "get_date": self.get_date,
            "get_partner_name": self.get_partner_name,
            "amount_word": self.amount_word,
            "get_footer_text": self.get_footer_text,
        }


class print_cheque_wizard(models.AbstractModel):
    _name = "report.dev_print_cheque.cheque_report"
    _description = "Print cheque From Account Move"

    def get_date(self, date):
        date = date.split("-")
        return date

    def amount_word(self, obj):
        if obj.partner_id and obj.partner_id.lang:
            amt_word = obj.with_context(
                lang=obj.partner_id.lang
            ).currency_id.amount_to_text(obj.amount)
        else:
            amt_word = obj.currency_id.amount_to_text(obj.amount)

        # Add Only in the end of the amount to words label
        if amt_word:
            amt_word += " Only"

        lst = amt_word.split(" ")

        lst_len = len(lst)
        amt_word_list = []

        for i in range(0, lst_len, obj.cheque_formate_id.word_in_f_line or lst_len):
            sublist = lst[i : i + obj.cheque_formate_id.word_in_f_line]
            amt_word_list.append(sublist)

        if obj.cheque_formate_id.is_star_word and amt_word_list:
            amt_word_list[0] += "***"
            amt_word_list[-1] += "***"

        return amt_word_list

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["cheque.wizard"].browse(data["form"])
        return {
            "doc_ids": docs.ids,
            "doc_model": "cheque.wizard",
            "docs": docs,
            "get_date": self.get_date,
            "amount_word": self.amount_word,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
