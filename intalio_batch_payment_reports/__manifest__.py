{
    'name': 'Intalio Batch Payment Reports',
    'summary': 'Intalio Batch Payment Reports',
    'category': 'Intalio',
    'version': '17.0.0.0.0',
    'description': """
    Vendor batch payment report should be export as the compatible with emirates NBD and RAK bank format.
    """,
    'author': 'Intalio, Hazem Essam El-DIN',
    'maintainer': 'Intalio, Hazem Essam El-DIN',
    'website': 'https://www.intalio.com',
    'depends': [
        'account_batch_payment',
        'report_xlsx',
    ],
    'data': [
        'views/account_batch_payment_views.xml',
        'report/account_batch_payment_xlsx.xml',
    ],
    'assets':
        {
            'web.assets_backend': [
                'intalio_batch_payment_reports/static/src/js/action_manager.js'
            ],
        },
    'license': 'LGPL-3',
}
