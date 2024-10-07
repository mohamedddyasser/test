{
    "name": "Intalio Sale Report File Rename",
    "summary": "Intalio Sale Report File Rename",
    "category": "Intalio",
    "version": "17.0.0.0.0",
    "description": """
    This module change in odoo sales report file name.
    """,
    "author": "Intalio, Hazem Essam El-DIN",
    "maintainer": "Intalio, Hazem Essam El-DIN",
    "website": "https://www.intalio.com",
    "depends": ["sale"],
    "data": [
        "report/ir_actions_report.xml",
    ],
    "uninstall_hook": "uninstall_hook",
    "license": "LGPL-3",
}
