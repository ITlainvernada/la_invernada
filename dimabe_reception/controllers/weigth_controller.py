from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


class WeightController(http.Controller):

    @http.route('/api/weight_reception', type='json', methods=['POST'], auth='token', cors='*')
    def set_weight(self, lot_name, weight_value, type_weight):
        if type_weight not in ['gross', 'tare']:
            raise UserError('Tipo de peso no corresponde a brutos o tara')
        picking_id = request.env['stock.picking'].sudo().search([('name', '=', lot_name)])
        if not picking_id:
            raise UserError('Lote no encontrado')
        if picking_id:
            if picking_id.picking_type_code != 'incoming':
                raise UserError('La operación seleccionada debe ser una recepción')
            if picking_id.state == 'done':
                raise UserError('El proceso de recepción ya fue finalizado')
            if type_weight == 'tare':
                if picking_id.gross_weight == 0:
                    raise UserError('Debe ingresa los kilos brutos')
                if picking_id.gross_weight <= weight_value:
                    raise UserError(
                        f'Los kilos tara no pueden ser mayores a los kilos bruto Kilos bruto : {picking_id.gross_weight}')
                picking_id.sudo().write({
                    'tare_weight': weight_value
                })
            if type_weight == 'gross':
                picking_id.write({
                    'gross_weight': weight_value
                })
            return {'message': f"Información ingresada a la recepción {lot_name}"}
