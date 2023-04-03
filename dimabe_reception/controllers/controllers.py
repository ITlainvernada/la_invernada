# -*- coding: utf-8 -*-
from odoo import http

# class Reception(http.Controller):
#     @http.route('/dimabe_reception/dimabe_reception/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dimabe_reception/dimabe_reception/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dimabe_reception.listing', {
#             'root': '/dimabe_reception/dimabe_reception',
#             'objects': http.request.env['dimabe_reception.dimabe_reception'].search([]),
#         })

#     @http.route('/dimabe_reception/dimabe_reception/objects/<model("dimabe_reception.dimabe_reception"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dimabe_reception.object', {
#             'object': obj
#         })