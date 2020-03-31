from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class PotentialLot(models.Model):
    _name = 'potential.lot'
    _description = 'posibles lotes para planificación de producción'

    name = fields.Char('lote', related='stock_production_lot_id.name')

    lot_product_id = fields.Many2one(
        'product.product',
        related='stock_production_lot_id.product_id'
    )

    lot_balance = fields.Float(
        related='stock_production_lot_id.balance',
        digits=dp.get_precision('Product Unit of Measure')
    )

    stock_production_lot_id = fields.Many2one('stock.production.lot', 'lote potencial')

    potential_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_potential_serial_ids',
    )

    consumed_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_consumed_serial_ids'
    )

    mrp_production_id = fields.Many2one('mrp.production', 'Producción')

    mrp_production_state = fields.Selection(
        string='estado',
        related='mrp_production_id.state'
    )

    qty_to_reserve = fields.Float(
        'Cantidad Reservada',
        compute='_compute_qty_to_reserve',
        digits=dp.get_precision('Product Unit of Measure')
    )

    is_reserved = fields.Boolean('Reservado')

    @api.multi
    def _compute_potential_serial_ids(self):
        for item in self:
            item.potential_serial_ids = item.stock_production_lot_id.stock_production_lot_serial_ids.filtered(
                lambda a: a.consumed is False and (
                            a.reserved_to_production_id == item.mrp_production_id or not a.reserved_to_production_id)
            )

    @api.multi
    def _compute_consumed_serial_ids(self):
        for item in self:
            item.consumed_serial_ids = item.stock_production_lot_id.stock_production_lot_serial_ids.filtered(
                lambda a: a.consumed and a.reserved_to_production_id == item.mrp_production_id
            )

    @api.model
    def get_stock_quant(self):
        return self.stock_production_lot_id.quant_ids.filtered(
            lambda a: a.location_id.name == 'Stock'
        )

    @api.model
    def get_production_quant(self):
        return self.stock_production_lot_id.quant_ids.filtered(
            lambda a: a.location_id.name == 'Production'
        )

    @api.multi
    def _compute_qty_to_reserve(self):
        for item in self:
            item.qty_to_reserve = sum(
                item.stock_production_lot_id.stock_production_lot_serial_ids.filtered(
                    lambda a: a.reserved_to_production_id == item.mrp_production_id
                ).mapped('display_weight')
            )

    @api.multi
    def reserve_stock(self):
        for item in self:
            serial_to_reserve = item.potential_serial_ids.filtered(lambda a: not a.reserved_to_production_id and not
                                                                   a.reserved_to_stock_picking_id)

            serial_to_reserve.with_context(mrp_production_id=item.mrp_production_id.id).reserve_serial()

            quant = item.get_stock_quant()

            quant.sudo().update({
                'reserved_quantity': quant.total_reserved
            })

            item.is_reserved = True

    @api.multi
    def confirm_reserve(self):

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def unreserved_stock(self):
        for item in self:
            serial_to_reserve = item.potential_serial_ids.filtered(
                lambda a: a.reserved_to_production_id == item.mrp_production_id
            )

            serial_to_reserve.unreserved_serial()

            item.is_reserved = item.qty_to_reserve > 0
