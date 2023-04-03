# -*- coding: utf-8 -*-
from odoo import http

# class DimabeReceptionCheck(http.Controller):
#     @http.route('/dimabe_reception_check/dimabe_reception_check/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dimabe_reception_check/dimabe_reception_check/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dimabe_reception_check.listing', {
#             'root': '/dimabe_reception_check/dimabe_reception_check',
#             'objects': http.request.env['dimabe_reception_check.dimabe_reception_check'].search([]),
#         })

#     @http.route('/dimabe_reception_check/dimabe_reception_check/objects/<model("dimabe_reception_check.dimabe_reception_check"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dimabe_reception_check.object', {
#             'object': obj
#         })