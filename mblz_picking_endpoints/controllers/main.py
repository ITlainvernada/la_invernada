from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
import json

class StockPickingController(http.Controller):

    @http.route('/api/v2/pickings', type='json', methods=['POST'], auth='public', cors='*')
    def get_pickings(self):
        token = request.httprequest.headers['AUTHORIZATION'].split(' ')[1]
        if token and token == request.env['ir.config_parameter'].sudo().get_param('mblz_picking_endpoints.token'):
            return json.dumps([{
                'name': 'P0024',
                'state': 'done'
            }], indent=1, ensure_ascii=False).encode('utf8')