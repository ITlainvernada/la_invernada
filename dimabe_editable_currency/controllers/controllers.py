# -*- coding: utf-8 -*-
from odoo import http

# class EditableCurrency(http.Controller):
#     @http.route('/dimabe_editable_currency/dimabe_editable_currency/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dimabe_editable_currency/dimabe_editable_currency/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dimabe_editable_currency.listing', {
#             'root': '/dimabe_editable_currency/dimabe_editable_currency',
#             'objects': http.request.env['dimabe_editable_currency.dimabe_editable_currency'].search([]),
#         })

#     @http.route('/dimabe_editable_currency/dimabe_editable_currency/objects/<model("dimabe_editable_currency.dimabe_editable_currency"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dimabe_editable_currency.object', {
#             'object': obj
#         })