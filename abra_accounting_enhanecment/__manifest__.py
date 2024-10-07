# -*- coding: utf-8 -*-
{
    'name': "abra_accounting_enhanecment",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'account_check_printing',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/receipt_voucher_report.xml',
        'data/invoices_report.xml',
        'views/account_payment_view.xml',
        'views/res_company_view.xml',
        'views/account_move_view.xml',
        'views/account_batch_payment_view.xml'
    ],
}
