# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Customers new Layout ",
    "version": "17.0.1.0.0",
    "category": " ",
    "description": """
        
    """,
    "author": "",
    "maintainer": "",
    "summary": " ",
    "website": " ",
    "depends": ["base", "account", "account_followup"],
    "data": [
        "security/ir.model.access.csv",
        "security/groups.xml",
        "data/approve_activity.xml",
        "views/res_bank_branch_view.xml",
        "views/res_partner_view.xml",
        "views/res_bank_view.xml",
        "views/res_partner_bank_view.xml",
        "views/account_types_view.xml",
        "views/report_followup.xml",
    ],
    "installable": True,
    "application": True,
}
