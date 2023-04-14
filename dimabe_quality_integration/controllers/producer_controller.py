from odoo import http, exceptions, models
from odoo.http import request
from datetime import date, timedelta
import werkzeug

class producer_controller(http.Controller):

    @http.route('/api/vat_producer_by_lot', type='json', methods=['GET'], auth='token', cors='*')
    def get_producer_by_lot(self, year=None):
        lot_ids = request.env['stock.production.lot'].search([('harvest', '=', year)])
        data = []

        for lot_id in lot_ids:
            data.append(
                {
                    'lot': lot_id.name,
                    'vat': lot_id.partner_id.document_number if lot_id.partner_id.document_number else lot_id.partner_id.client_identifier_value if lot_id.partner_id.client_identifier_value else ''
                }
            )

        return data