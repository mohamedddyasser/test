# -*- coding: utf-8 -*-
{
    "name": "Odoo Invoice Analysis Dashboard",
    "version": "17.0.1.0.0",
    "category": "project",
    "summary": """
    """,
    "description": """
    """,
    "author": "Intalio",
    "depends": ["account_accountant"],
    "data": ["views/views.xml"],
    "assets": {
        "web.assets_backend": [
            "invoice_analysis_dashboard/static/src/css/dashboard.css",
            "invoice_analysis_dashboard/static/src/lib/chart.js",
            "invoice_analysis_dashboard/static/src/js/helper.js",
            "invoice_analysis_dashboard/static/src/js/dashboard.js",
            "invoice_analysis_dashboard/static/src/xml/dashboard.xml",
        ]
    },
    "images": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
