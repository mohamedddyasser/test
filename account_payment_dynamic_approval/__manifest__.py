# -*- coding: utf-8 -*-
{
    'name': 'Account Payment Dynamic Approval',
    'summary': 'Allow to request approval based on approval matrix',
    'author': 'Ever Business Solutions',
    'maintainer': 'Abdalla Mohamed',
    'website': 'https://www.everbsgroup.com/',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'license': 'OPL-1',
    'depends': [
        'base_dynamic_approval',
        'account_payment',
        # 'account_batch_payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/confirm_account_payment_wizard.xml',
        # 'views/account_payment.xml',
        'views/account_move.xml',
        'views/batch_payment.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
