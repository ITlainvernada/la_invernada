# -*- coding: utf-8 -*-
from odoo import http

# class ExportOrderDimabe(http.Controller):
#     @http.route('/dimabe_export_order/dimabe_export_order/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dimabe_export_order/dimabe_export_order/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dimabe_export_order.listing', {
#             'root': '/dimabe_export_order/dimabe_export_order',
#             'objects': http.request.env['dimabe_export_order.dimabe_export_order'].search([]),
#         })

#     @http.route('/dimabe_export_order/dimabe_export_order/objects/<model("dimabe_export_order.dimabe_export_order"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dimabe_export_order.object', {
#             'object': obj
#         })