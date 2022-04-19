from odoo import fields, models, api


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _prepare_move_default_values(self, return_line, new_picking):
        res = super(StockReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        new_picking.write({
            'is_return': True
        })
        return res

    def _create_returns(self):
        res = super(StockReturnPicking, self)._create_returns()
        if res:
            self.picking_id.write({
                'is_returned': True
            })
            picking = self.env['stock.picking'].sudo().search([('id', '=', res[0])])
            picking.move_line_ids_without_package.sudo().unlink()
            for line in self.product_return_moves:
                lot_id = self.picking_id.move_line_ids_without_package.filtered(
                    lambda x: x.product_id.id == line.product_id.id).lot_id
                self.env['stock.move.line'].create({
                    'product_id': line.product_id.id,
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'lot_id': lot_id.id if lot_id else None,
                    'qty_done': line.quantity,
                    'product_uom_id': line.uom_id.id,
                    'move_id': picking.move_ids_without_package.filtered(
                        lambda x: x.product_id.id == line.product_id.id).id
                })
        return res
