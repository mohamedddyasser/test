# -*- coding: utf-8 -*-
{
    'name': "Abra Credit Note Reports",
    'summary': "Credit Note Reports",
    'author': "MohamedSalah",
    'website': "https://www.yourcompany.com",
    'category': 'Account',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],
    'data': [
        'views/views.xml',
        'reports/credit_note_report.xml',
    ],
    'installable': False,
}

