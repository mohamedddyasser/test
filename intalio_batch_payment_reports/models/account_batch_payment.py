# -*- coding: utf-8 -*-
from odoo import models


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    def account_batch_payment_report_excel_1(self):
        data = {}
        return self.env.ref('intalio_batch_payment_reports.action_batch_payment_xlsx_report1').report_action(self,
                                                                                                             data=data)

    def account_batch_payment_report_excel_2(self):
        data = {}
        return self.env.ref('intalio_batch_payment_reports.action_batch_payment_xlsx_report2').report_action(self,
                                                                                                             data=data)

    def account_batch_payment_report_excel_3(self):
        data = {}
        return self.env.ref('intalio_batch_payment_reports.action_batch_payment_xlsx_report3').report_action(self,
                                                                                                             data=data)


class ReportXlsxAbstract1(models.AbstractModel):
    _name = "report.intalio_batch_payment_reports.report_batch_payment_xlsx1"
    _inherit = "report.report_xlsx.abstract"
    _description = "Batch Payment XLSX Report"

    def generate_xlsx_report(self, workbook, data, batch_payment):
        sheet = workbook.add_worksheet('Account Batch Payment')

        sheet.set_column(0, 6, 30)
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '13px'})

        sheet.write(0, 0, 'Default value - "BPF"')
        sheet.write(0, 1, 'Length - 13')
        sheet.write(0, 2, 'Length - 64')
        sheet.write(0, 3, 'Length - 13')
        sheet.write(0, 4, 'Length - 3')
        sheet.write(0, 5, 'Length - 15')
        sheet.write(0, 6, 'Length - 50')

        sheet.merge_range(1, 0, 1, 6, data='Template starts from ROW 3 below', cell_format=head)

        sheet.write(2, 0, 'TRANSACTION TYPE IDENTIFIER')
        sheet.write(2, 1, 'DEBIT ACCOUNT NUMBER')
        sheet.write(2, 2, 'BENEFICIARY NICKNAME')
        sheet.write(2, 3, 'CREDIT ACCOUNT NUMBER')
        sheet.write(2, 4, 'TRANSACTION CURRENCY')
        sheet.write(2, 5, 'TRANSACTION AMOUNT')
        sheet.write(2, 6, 'PAYMENT DETAILS')


class ReportXlsxAbstract2(models.AbstractModel):
    _name = "report.intalio_batch_payment_reports.report_batch_payment_xlsx2"
    _inherit = "report.report_xlsx.abstract"
    _description = "Batch Payment XLSX Report"

    def generate_xlsx_report(self, workbook, data, batch_payment):
        sheet = workbook.add_worksheet('Account Batch Payment')
        sheet.set_column(0, 20, 30)

        sheet.write(0, 0, 'Customer Reference No')
        sheet.write(0, 1, 'Transaction Currency')
        sheet.write(0, 2, 'Transaction Amount')
        sheet.write(0, 3, 'Transaction Type Code')
        sheet.write(0, 4, 'Beneficiary Name')
        sheet.write(0, 5, 'TRANSACTION AMOUNT')
        sheet.write(0, 6, 'Beneficiary Addr. Line 1')
        sheet.write(0, 7, 'Beneficiary Addr. Line 2')
        sheet.write(0, 8, 'Beneficiary Addr. Line 3')
        sheet.write(0, 9, 'Beneficiary Country')
        sheet.write(0, 10, 'Beneficiary E-mail Id')
        sheet.write(0, 11, 'Beneficiary Account No.')
        sheet.write(0, 12, 'Beneficiary Bank Swift Code')
        sheet.write(0, 13, 'Intermediatory Bank Swift Code')
        sheet.write(0, 14, 'Charge Type')
        sheet.write(0, 15, 'Purpose Code')
        sheet.write(0, 16, 'Beneficiary Purpose Code')
        sheet.write(0, 17, 'Purpose Of Payment')
        sheet.write(0, 18, 'Routing Code')
        sheet.write(0, 19, 'Deal Reference No')
        sheet.write(0, 20, 'Account Identifier')


class ReportXlsxAbstract3(models.AbstractModel):
    _name = "report.intalio_batch_payment_reports.report_batch_payment_xlsx3"
    _inherit = "report.report_xlsx.abstract"
    _description = "Batch Payment XLSX Report"

    def generate_xlsx_report(self, workbook, data, batch_payment):
        sheet = workbook.add_worksheet('Account Batch Payment')
        sheet.set_column(0, 20, 30)

        cell_format = workbook.add_format({'font_name': 'Calibri', 'bold': True, 'font_size': '11px'})

        sheet.write(7, 0, 'Account Statement', cell_format)
        sheet.write(8, 0, 'User Name:', cell_format)
        sheet.write(9, 0, 'Date:', cell_format)
        sheet.write(10, 0, 'Company Name', cell_format)
        sheet.write(11, 0, 'Account Name', cell_format)
        sheet.write(12, 0, 'Filters', cell_format)
        sheet.write(13, 0, 'Date Order', cell_format)
        sheet.write(14, 0, 'Date Order', cell_format)
        sheet.write(15, 0, 'Total Credit Transactions', cell_format)
        sheet.write(16, 0, 'Total Debit Amount', cell_format)
        sheet.write(17, 0, 'Account Number', cell_format)
        sheet.write(18, 0, 'Total Credit Amount', cell_format)
        sheet.write(19, 0, 'Processing Time', cell_format)
        sheet.write(20, 0, 'Credit/Debit', cell_format)
        sheet.write(21, 0, 'Results per page', cell_format)
        sheet.write(22, 0, 'Date To', cell_format)
        sheet.write(23, 0, 'Date From', cell_format)
        sheet.write(24, 0, 'Transaction Type', cell_format)
        sheet.write(25, 0, 'Total Debit Transactions', cell_format)
