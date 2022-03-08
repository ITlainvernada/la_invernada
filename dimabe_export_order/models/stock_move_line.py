from odoo import fields, models, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    lot_serial = fields.Many2many(comodel_name='stock.production.lot.serial', compute='get_serial')

    @api.multi
    def get_serial(self):
        for item in self:
            if item.lot_id:
                serials = self.env['stock.production.lot.serial'].search(
                    [('stock_production_lot_id.id', '=', item.lot_id.id)])
                item.lot_serial = serials
