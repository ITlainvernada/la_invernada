from odoo import http, exceptions, models
from odoo.http import request
from datetime import date, timedelta
import werkzeug


class producer_controller(http.Controller):

    @http.route('/api/vat_producer_by_lot', type='json', methods=['GET'], auth='token', cors='*')
    def get_producer_by_lot(self, lot=None):
        partner_id = self.env['stock.production.lot'].search([('name', '=', lot)]).producer_id
        vat = ''
        if partner_id:
            vat = partner_id.document_number if partner_id.document_number else partner_id.client_identifier_value
        
        return vat
