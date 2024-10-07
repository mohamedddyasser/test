{
    "name": "Intalio Report Templates",
    "summary": "Intalio Report Templates",
    "category": "Intalio",
    "version": "17.0.0.0.0",
    "description": """
    This module change in odoo report templates.
    """,
    "author": "Intalio, Hazem Essam El-DIN",
    "website": "https://www.intalio.com",
    "depends": [
        "web",
    ],
    "data": [
        "views/report_templates.xml",
    ],
    "license": "LGPL-3",
    "assets": {
        "web.report_assets_common": [
            "intalio_report_templates/static/src/webclient/actions/reports/layout_assets/layout_boxed.scss",
        ],
    },
}
