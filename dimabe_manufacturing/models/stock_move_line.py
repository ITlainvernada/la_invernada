from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.pycompat import izip
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from odoo.addons import decimal_precision as dp
from datetime import datetime


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    count_stock_production_lot_serial = fields.Integer(
        'Total Bultos',
        compute='_compute_count_stock_production_lot_serial'
    )

    is_raw = fields.Boolean('Es Subproducto')

    tmp_qty_done = fields.Float(
        'Realizado',
        digits=dp.get_precision('Product Unit of Measure')
    )

    sale_order_id = fields.Many2one('sale.order', 'Orden')

    @api.multi
    def _compute_count_stock_production_lot_serial(self):
        for item in self:
            if item.lot_id:
                item.count_stock_production_lot_serial = len(item.lot_id.stock_production_lot_serial_ids)

    def _action_done(self):
        for ml in self:
            try:
                if ml.location_id.usage == 'production' or ml.location_dest_id.usage == 'production':
                    if ml.location_id.usage == 'production':
                        if ml.lot_id:
                            ml.lot_id.get_and_update(ml.product_id.id)
                        ml.write({
                            'state': 'done'
                        })
                else:
                    res = super(StockMoveLine, self)._action_done()
                    return res
            except:
                ml.write({
                    'product_uom_qty': 0,
                    'state': 'done'
                })
                ml.lot_id.update_stock_quant(location_id=ml.location_id.id)

    def fix_move_line_suplly(self):
        lines = self.env['stock.move.line'].search(
            [('state', '=', 'done'), ('move_id.raw_material_production_id', '!=', False)])
        line_suplly = lines.filtered(lambda x: not x.move_id.needs_lots and x.product_id.tracking != 'lot' and x.write_date.month >= 6 and x.write_date.year == 2021)
        for suplly in line_suplly.mapped('location_id'):
            products = line_suplly.filtered(lambda x: x.location_id.id == suplly.id).mapped('product_id')
            line_location = line_suplly.filtered(lambda x: x.location_id.id == suplly.id)
            for product in products:
                quant = self.env['stock.quant'].search(
                    [('product_id.id', '=', product.id), ('location_id.id', '=', suplly.id)])
                if quant:
                    quant.write({
                        'quantity': quant.quantity - sum(
                            line_location.filtered(lambda x: x.product_id.id == product.id).mapped('qty_done'))
                    })
                else:
                    self.env['stock.quant'].sudo().create({
                        'quantity': 0 - sum(
                            line_location.filtered(lambda x: x.product_id.id == product.id).mapped('qty_done')),
                        'location_id': suplly.id,
                        'product_id': product.id,
                        'in_date': datetime.now()
                    })
