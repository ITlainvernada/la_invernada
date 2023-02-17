from odoo import models, fields, api


class DeletePickingLot(models.Model):
    _name = 'delete.picking.lot'
    _rec_name = 'picking_name'

    picking_name = fields.Char('Operación')

    picking_id = fields.Many2one('stock.picking', string='Recepción')

    picking_type_id = fields.Many2one('stock.picking.type', string="Tipo de operación")

    lot_name = fields.Char('Lote')

    reason = fields.Html('Razón')

    message = fields.Html('Mensaje', compute='compute_message')

    user_id = fields.Many2one('res.users', string='Usuario')

    def compute_message(self):
        for item in self:
            message = f'<h3>¿Esta seguro de eliminar la recepción {item.picking_name} y el lote {item.lot_name}?</h3> <br/>'
            item.message = message

    def delete_picking(self):
        for item in self:
            item.validate_picking()
            lot_id = item.picking_id.move_line_ids_without_package.mapped('lot_id')
            if lot_id:
                lot_id.quant_ids.sudo().unlink()
                lot_id.sudo().unlink()
            item.picking_id.move_line_ids_without_package.write({
                'picking_id': None,
                'reference': f'Eliminado ({item.picking_id.name})'
            })
            item.picking_id.move_ids_without_package.write({
                'picking_id': None,
                'reference': f'Eliminado ({item.picking_id.name})'
            })
            item.picking_id.sudo().unlink()
            action_id = self.env.ref('stock.stock_picking_action_picking_type').read()[0]
            return {
                'name': action_id['name'],
                'type': action_id['type'],
                'res_model': action_id['res_model'],
                'target': 'fullscreen',
                'search_view_id': action_id['search_view_id'][0],
                'context': str({'search_default_picking_type_id': item.picking_type_id.id,
                                'default_picking_type_id': item.picking_id.id,
                                'contact_display': 'partner_address'
                                }),
                'view_mode': action_id['view_mode']
            }

    def validate_picking(self):
        for item in self:
            if not self.env.user.has_group('dimabe_reception.group_modify_delete_picking'):
                raise models.UserError('Su usuario no cuenta con los permisos para realizar esta acción')
            lot_ids = item.picking_id.move_line_ids_without_package.filtered(lambda x: x.lot_id).mapped('lot_id')
            for lot in lot_ids:
                if any(serial.consumed for serial in lot.stock_production_lot_serial_ids):
                    raise models.ValidationError(f'El lote {lot.name} ya uso en un proceso productivo')