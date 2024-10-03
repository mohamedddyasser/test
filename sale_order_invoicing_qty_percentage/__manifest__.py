# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sales order invoicing by percentage of the quantity",
    "version": "17.0.0.0",
    "category": "Sales Management",
    "license": "AGPL-3",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-invoicing",
    "depends": ["sale", "abra_accounting_enhanecment"],
    "data": ["wizards/sale_advance_payment_inv_views.xml"],
    "installable": True,
    "maintainers": ["pedrobaeza"],
}
