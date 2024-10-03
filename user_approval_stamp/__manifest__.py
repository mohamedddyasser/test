# -*- coding: utf-8 -*-
{
    'name': "User Approval Stamp",
    'summary': """ User Approval Stamp """,
    'description': """ """,
    'author': "Intalio",
    'category': 'Uncategorized',
    'version': '17.0.1.0.0',
    'depends': ['base', 'base_dynamic_approval'],
    'data': [
        'security/approval_stamp_security.xml',
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'wizards/approve_dynamic_approval_wizard.xml',
    ],
}
