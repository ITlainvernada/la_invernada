from odoo import http, exceptions, models
from odoo.http import request
from datetime import date, timedelta
import werkzeug

class producer_controller(http.Controller):

    @http.route('/api/vat_producer_by_year', type='json', methods=['GET'], auth='token', cors='*')
    def get_producer_by_lot(self, year=None):
        lot_ids = request.env['stock.production.lot'].search([('harvest', '=', year), ('is_prd_lot', '=', False)])
        data = []

        for lot_id in lot_ids:
            vat = ''
            if lot_id.producer_id.document_number:
                vat = lot_id.producer_id.document_number
            if not vat and lot_id.producer_id.client_identifier_value:
                vat = lot_id.producer_id.client_identifier_value
            data.append(
                {
                    'lot': lot_id.name,
                    'vat': vat
                }
            )

        return data

    @http.route('/api/vat_producer_by_lot', type='json', methods=['GET'], auth='token', cors='*')
    def get_producer_by_lot(self, lot=None):
        lot_id = request.env['stock.production.lot'].search([('name', '=', lot), ('is_prd_lot', '=', False)])[0]
        data = []

        vat = ''
        if lot_id.producer_id.document_number:
            vat = lot_id.producer_id.document_number
        if not vat and lot_id.producer_id.client_identifier_value:
            vat = lot_id.producer_id.client_identifier_value

        return vat