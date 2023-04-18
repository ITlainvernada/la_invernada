from odoo import http
from odoo.http import request


class WeightController(http.Controller):

    @http.route('/api/weight_reception', type='json', methods=['GET'], auth='token', cors='*')
    def set_weight(self, lot_name, weight_value, type_weight):
        if type_weight not in ['gross', 'tare']:
            return {'message': 'Tipo de peso no corresponde a brutos o tara'}
        picking_id = request.env['stock.picking'].sudo().search([('name', '=', lot_name)])
        if not picking_id:
            return {'message': 'Lote no encontrado'}
        if picking_id:
            if picking_id.picking_type_code != 'incoming':
                return {'message': 'La operación seleccionada debe ser una recepción'}
            if picking_id.state == 'done':
                raise {'message': 'Proceso de recepción finalizado'}
            if type_weight == 'tare':
                if picking_id.gross_weight == 0:
                    return {'message': 'Debe ingresa los kilos bruto'}
                picking_id.sudo().write({
                    'tare_weight': weight_value
                })
            if type_weight == 'gross':
                picking_id.write({
                    'gross_weight': weight_value
                })
            return {'message': f"Información ingresada a la recepción {lot_name}"}
