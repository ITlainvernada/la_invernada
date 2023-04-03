# -*- coding: utf-8 -*-
from odoo import http

# class DimabePurchaseProcess(http.Controller):
#     @http.route('/dimabe_purchase_process/dimabe_purchase_process/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dimabe_purchase_process/dimabe_purchase_process/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dimabe_purchase_process.listing', {
#             'root': '/dimabe_purchase_process/dimabe_purchase_process',
#             'objects': http.request.env['dimabe_purchase_process.dimabe_purchase_process'].search([]),
#         })

#     @http.route('/dimabe_purchase_process/dimabe_purchase_process/objects/<model("dimabe_purchase_process.dimabe_purchase_process"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dimabe_purchase_process.object', {
#             'object': obj
#         })