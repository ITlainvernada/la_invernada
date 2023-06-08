from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
import json

class StockPickingController(http.Controller):
    def _get_container_info(self, moves, key):
        for move in moves:
            if not move.variety:
                if key == 'product_name':
                    return '%s (%s) kg' % (move.product_id.name, move.product_id.weight)
                elif key == 'weight':
                    return move.product_id.weight
                return move[key]
            
    def _get_variety_info(self, moves, key):
        names = []
        for move in moves:
            if move.product_id.categ_id.is_mp:
                if key in ['default_code', 'display_name']:
                    names.append(move.product_id[key])
                elif move[key]:
                    names.append(move[key])
        return '/'.join(names)
    
    def _get_dry_kgs(self, picking_id):
        if 'verde' not in str.lower(picking_id.picking_type_id.warehouse_id.name):
            ##  kg netos - kg calidad para materia prima seca
            return picking_id.net_weight - picking_id.quality_weight
        domain = [
            ('state', 'in', ['done', 'process'])
        ]
        dried_process_id = request.env['unpelled.dried'].sudo().search(domain).filtered(lambda dp: picking_id.name in dp.in_lot_ids.mapped('name'))
        if dried_process_id:
            output_lot_name = dried_process_id.out_lot_id.name
            output_picking_id = request.env['stock.picking'].sudo().search([('name', '=', output_lot_name)])
            if output_picking_id:
                return output_picking_id.net_weight - output_picking_id.quality_weight
    
    def _get_picking_data(self, picking_ids):
        return [{
                # 'ID_SQL': picking_id.id,
                'ProducerCode': picking_id.partner_id.sag_code,
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
                'DryKgs': self._get_dry_kgs(picking_id), 
                # 'QualityGreenId': 'N/A',
                'ContainerWeight': self._get_container_info(picking_id.move_ids_without_package, 'weight'), ##peso del contenedor desde el procuto
                'OdooUpdated': picking_id.write_date.strftime('%Y-%m-%d %H:%M:%S'),
                # 'UpdatedAt': 'N/A'  
            } for picking_id in picking_ids]
    
    def _get_lot_ids(self, process_id):
        
        return '|'.join(process_id.in_lot_ids.mapped('name'))
    
    def _get_process_data(self, process_ids):
        return [{
            'name': process_id.name,
            'InitDate': process_id.create_date.strftime('%Y-%m-%d %H:%M:%S'),
            'LotIds': self._get_lot_ids(process_id),
            'state': process_id.state,
            'ProductName': process_id.product_in_id.name,
            'ProductId': process_id.product_in_id.id,
            'oven_use_ids': [{
                'name': oven_use_id.name,
                'init_date': oven_use_id.init_date.strftime('%Y-%m-%d %H:%M:%S'),
                'finish_date': oven_use_id.finish_date.strftime('%Y-%m-%d %H:%M:%S'),
                'used_lot_id': oven_use_id.used_lot_id.name,
                'state': oven_use_id.state
                
                
                
            } for oven_use_id in process_id.oven_use_ids]
            
        } for process_id in process_ids]
    
    @http.route('/api/v2/producers', type='json', methods=['POST'], auth='public', cors='*')
    def get_producers(self):
        token = request.httprequest.headers['AUTHORIZATION'].split(' ')[1]
        if token and token == request.env['ir.config_parameter'].sudo().get_param('mblz_picking_endpoints.token'):
            limit = None
            decoded_data = request.httprequest.data.decode('utf-8')
            data = json.loads(decoded_data)
            if data:
                limit = data.get('limit')
            domain = [('supplier', '=', True)]
            partner_ids = request.env['res.partner'].sudo().search(domain, limit=limit)
            return json.dumps({
                    'count': len(partner_ids),
                    'records': [{
                        'odooId': partner_id.id,
                        'name': partner_id.name,
                        'producerCode': partner_id.sag_code
                    } for partner_id in partner_ids]
                }, ensure_ascii=False)

    @http.route('/api/v2/pickings', type='json', methods=['POST'], auth='public', cors='*')
    def get_pickings(self):
        token = request.httprequest.headers['AUTHORIZATION'].split(' ')[1]
        if token and token == request.env['ir.config_parameter'].sudo().get_param('mblz_picking_endpoints.token'):
            limit = None
            decoded_data = request.httprequest.data.decode('utf-8')
            data = json.loads(decoded_data)
            if data:
                limit = data.get('limit')
                if data.get('date'):
                    domain = [
                        ('state', 'in', ['done']), 
                        ('picking_type_code', '=', 'incoming'),
                        ('date_done', '>=', data.get('date'))
                        ]
                    if data.get('producerId'):
                        domain.append(('partner_id', '=', int(data.get('producerId'))))
                    picking_ids = request.env['stock.picking'].sudo().search(domain, limit=limit)
                    return json.dumps({
                            'count': len(picking_ids),
                            'records': self._get_picking_data(picking_ids)
                        }, ensure_ascii=False)
    
    @http.route('/api/v2/dried_process', type='json', methods=['POST'], auth='public', cors='*')
    def get_dried_process(self):
        token = request.httprequest.headers['AUTHORIZATION'].split(' ')[1]
        if token and token == request.env['ir.config_parameter'].sudo().get_param('mblz_picking_endpoints.token'):
            limit = None
            decoded_data = request.httprequest.data.decode('utf-8')
            data = json.loads(decoded_data)
            if data:
                limit = data.get('limit')
                if data.get('date'):
                    domain = [
                        ('state', 'in', ['done', 'process']), 
                        ('create_date', '>=', data.get('date')),
                        ]
                    if data.get('producerId'):
                        domain.append(('producer_id', '=', int(data.get('producerId'))))
                    process_ids = request.env['unpelled.dried'].sudo().search(domain, limit=limit)
                    return json.dumps({
                            'count': len(process_ids),
                            'records': self._get_process_data(process_ids)
                        }, ensure_ascii=False)