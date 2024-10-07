# -*- coding: utf-8 -*-
# from odoo import http


# class AbraAccountingEnhanecment(http.Controller):
#     @http.route('/abra_accounting_enhanecment/abra_accounting_enhanecment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/abra_accounting_enhanecment/abra_accounting_enhanecment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('abra_accounting_enhanecment.listing', {
#             'root': '/abra_accounting_enhanecment/abra_accounting_enhanecment',
#             'objects': http.request.env['abra_accounting_enhanecment.abra_accounting_enhanecment'].search([]),
#         })

#     @http.route('/abra_accounting_enhanecment/abra_accounting_enhanecment/objects/<model("abra_accounting_enhanecment.abra_accounting_enhanecment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('abra_accounting_enhanecment.object', {
#             'object': obj
#         })
