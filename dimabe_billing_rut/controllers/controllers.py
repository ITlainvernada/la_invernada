# -*- coding: utf-8 -*-
from odoo import http

# class DimabeBillingRut(http.Controller):
#     @http.route('/dimabe_billing_rut/dimabe_billing_rut/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dimabe_billing_rut/dimabe_billing_rut/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dimabe_billing_rut.listing', {
#             'root': '/dimabe_billing_rut/dimabe_billing_rut',
#             'objects': http.request.env['dimabe_billing_rut.dimabe_billing_rut'].search([]),
#         })

#     @http.route('/dimabe_billing_rut/dimabe_billing_rut/objects/<model("dimabe_billing_rut.dimabe_billing_rut"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dimabe_billing_rut.object', {
#             'object': obj
#         })