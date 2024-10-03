# -*- coding: utf-8 -*-
{
    'name': "Abra Customer Statement Report",
    'description': """
        Abra Customer Statement Report
    """,
    'author': "Intalio",
    'category': 'Accounting',
    'version': '17.0',

    'depends': ['base','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'wizard/customer_statement_report.xml',
        'wizard/customer_payment.xml',
        'reports/customer_statement_report.xml',
        'reports/customer_payment_report.xml',
    ],

}

