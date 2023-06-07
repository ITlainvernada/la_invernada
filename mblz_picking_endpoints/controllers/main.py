from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
import json

class StockPickingController(http.Controller):
    def _get_container_info(self, moves, key):
        for move in moves:
            if not move.variety:
                if key == 'product_name':
                    return move.product_id.name
                return move[key]
            
    def _get_variety_info(self, moves, key):
        names = []
        for move in moves:
            if key in ['default_code', 'display_name']:
                names.append(move.product_id[key])
            elif move[key]:
                names.append(move[key])
        return '/'.join(names)
    
    def _get_picking_data(self, picking_ids):
        return [{
                # 'ID_SQL': picking_id.id,
                'ProducerCode': picking_id.sag_code,
                'ProducerName': picking_id.partner_id.name,
                'VarietyName': self._get_variety_info(picking_id.move_ids_without_package, 'variety'),
                'LotNumber': picking_id.name,
                'DispatchGuideNumber': picking_id.guide_number,
                'ReceptionDate': picking_id.date_done.strftime('%Y-%m-%d %H:%M:%S'), ##TODO
                'ReceptionKgs': picking_id.gross_weight,
                'Season': picking_id.harvest,
                'QualityNumber': 'N/A', ##TODO
                # 'Warehouse': picking_id.location_dest_id.name,
                'QualityWeight': picking_id.quality_weight,
                'ContainerQuantity': self._get_container_info(picking_id.move_ids_without_package, 'quantity_done'),
                'ContainerWeightAverage': picking_id.avg_unitary_weight,
                # 'Observation': picking_id.note,
                'Tare': picking_id.tare_weight,
                'ContainerType': self._get_container_info(picking_id.move_ids_without_package, 'product_name'),
                'ArticleCode': self._get_variety_info(picking_id.move_ids_without_package, 'default_code'),
                'ArticleDescription': self._get_variety_info(picking_id.move_ids_without_package, 'display_name'),
                'DryKgs': 'N/A', ##  kg netos - kg calida para materia primea seca
                # 'QualityGreenId': 'N/A',
                'ContainerWeight': 'N/A', ##peso del contenedor desde el procuto
                'OdooUpdated': picking_id.write_date.strftime('%Y-%m-%d %H:%M:%S'),
                # 'UpdatedAt': 'N/A'  
            } for picking_id in picking_ids]
    
    @http.route('/api/v2/producers', type='json', methods=['GET'], auth='public', cors='*')
    def get_producers(self):
        token = request.httprequest.headers['AUTHORIZATION'].split(' ')[1]
        if token and token == request.env['ir.config_parameter'].sudo().get_param('mblz_picking_endpoints.token'):
            limit = None
            decoded_data = request.httprequest.data.decode('utf-8')
            data = json.loads(decoded_data)
            if data:
                limit = data.get('limit')
            domain = [('suppplier', '=', True)]
            partner_ids = request.env['res.partner'].sudo().search(domain, limit=limit)
            return json.dumps([{
                    'odooId': partner_id.id,
                    'name': partner_id.name,
                    'producerCode': partner_id.sag_code
                } for partner_id in partner_ids], ensure_ascii=False)

    @http.route('/api/v2/pickings', type='json', methods=['POST'], auth='public', cors='*')
    def get_pickings(self):
        token = request.httprequest.headers['AUTHORIZATION'].split(' ')[1]
        if token and token == request.env['ir.config_parameter'].sudo().get_param('mblz_picking_endpoints.token'):
            decoded_data = request.httprequest.data.decode('utf-8')
            data = json.loads(decoded_data)
            
            domain = [('state', 'in', ['done']), ('picking_type_code', '=', 'incoming')]
            picking_ids = request.env['stock.picking'].sudo().search(domain, limit=100)
            return json.dumps(self._get_picking_data(picking_ids), ensure_ascii=False)
    
    # @http.route('/api/v2/picking_ids', type='json', methods=['POST'], auth='public', cors='*')
    # def get_pickings(self):
    #     token = request.httprequest.headers['AUTHORIZATION'].split(' ')[1]
    #     if token and token == request.env['ir.config_parameter'].sudo().get_param('mblz_picking_endpoints.token'):
    #         domain = [('state', 'in', ['done']), ('picking_type_code', '=', 'incoming')]
    #         picking_ids = request.env['stock.picking'].sudo().search(domain, limit=100)
    #         return json.dumps({
    #             'ids': picking_ids.ids}, ensure_ascii=False)