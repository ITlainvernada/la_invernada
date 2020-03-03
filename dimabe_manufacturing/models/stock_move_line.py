from odoo import fields, models, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    count_stock_production_lot_serial = fields.Integer(
        'Total Bultos',
        compute='_compute_count_stock_production_lot_serial'
    )

    is_raw = fields.Boolean('Es Subproducto')

    tmp_qty_done = fields.Float('Realizado')

    lot_serial = fields.Many2many('stock_production_lot_serial',compute='get_serial')
    
    @api.multi
    def get_serial(self):
        for item in self:
            if item.lot_id:
                for serial in item.stock_production_lot_serial_ids:
                    models._logger.error(serial.id)


    @api.multi
    def _compute_count_stock_production_lot_serial(self):
        for item in self:
            if item.lot_id:
                item.count_stock_production_lot_serial = len(item.lot_id.stock_production_lot_serial_ids)
