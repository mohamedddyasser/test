{
    'name': 'Intalio Sale',
    'summary': 'Intalio Sale',
    'category': 'Intalio',
    'version': '17.0.0.0.0',
    'description': """
    This module change in odoo sales.
    """,
    'author': 'Intalio, Hazem Essam El-DIN',
    'maintainer': 'Intalio, Hazem Essam El-DIN',
    'website': 'https://www.intalio.com',
    'depends': [
        'sale'
    ],
    'data': [
        'report/ir_actions_report_templates.xml',
        'report/pdf_quote_report.xml',
        'views/sale_order_views.xml',
    ],
    'license': 'LGPL-3',
}
