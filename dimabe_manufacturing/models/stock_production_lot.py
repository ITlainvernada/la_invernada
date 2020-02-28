from odoo import fields, models, api


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    is_prd_lot = fields.Boolean('Es Lote de salida de Proceso')

    is_standard_weight = fields.Boolean('Series Peso Estandar')

    standard_weight = fields.Float('Peso Estandar')

    qty_standard_serial = fields.Integer('Cantidad de Series')

    stock_production_lot_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        'stock_production_lot_id',
        string="Detalle"
    )

    total_serial = fields.Float(
        'Total',
        compute='_compute_total_serial'
    )

    qty_to_reserve = fields.Float('Cantidad a Reservar')

    reserve = fields.Float('Cantidad deseada')

    @api.multi
    def _compute_total_serial(self):
        for item in self:
            item.total_serial = sum(item.stock_production_lot_serial_ids.mapped('display_weight'))

    @api.multi
    def reserved(self):
        for item in self:
            if item.qty_standard_serial == 0:
                if 'stock_picking_id' in self.env.context:
                    stock_picking_id = self.env.context['stock_picking_id']
                    reserve = self.env.context['reserved']
                    models._logger.error(reserve)
                    stock_picking = self.env['stock.picking'].search([('id', '=', stock_picking_id)])
                    if stock_picking:
                        stock_move = stock_picking.move_ids_without_package.filtered(
                            lambda x: x.product_id == item.product_id
                        )
                        stock_quant = item.get_stock_quant()
                        stock_quant.sudo().update({
                            'reserved_quantity': stock_quant.reserved_quantity + item.qty_to_reserve
                        })
                        move_line = self.env['stock.move.line'].create({
                            'product_id': item.product_id.id,
                            'lot_id': item.id,
                            'product_uom_qty': reserve,
                            'product_uom_id': stock_move.product_uom.id,
                            'location_id': stock_quant.location_id.id,
                            'location_dest_id': stock_picking.partner_id.property_stock_customer.id
                        })
                        stock_move.sudo().update({
                            'move_line_ids': [
                                (4, move_line.id)
                            ]
                        })

    @api.multi
    def unreserved(self):
        for item in self:
            if item.qty_standard_serial == 0:
                models._logger.error(self.env.context['stock_picking_id'])
                stock_picking_id = self.env.context['stock_picking_id']
                stock_picking = self.env['stock.picking'].search([('id','=',stock_picking_id)])
            if stock_picking:
                stock_move = stock_picking.move_ids_without_package.filtered(
                    lambda x: x.product_id == item.product_id
                )
                models._logger.error(stock_move)
                move_line = stock_move.move_line_ids.filtered(
                    lambda a: a.lot_id.id == item.id and a.product_qty == stock_move.product_uom_qty
                )
                models._logger.error(move_line)
                stock_quant = item.get_stock_quant()
                stock_quant.sudo().update({
                    'reserved_quantity': stock_quant.reserved_quantity - stock_move.product_uom_qty
                })

                for ml in move_line:
                    ml.write({'move_id': None, 'product_uom_qty': 0})

    @api.multi
    def write(self, values):
        for item in self:
            res = super(StockProductionLot, self).write(values)
            counter = 0
            if not item.is_standard_weight:
                for serial in item.stock_production_lot_serial_ids:
                    counter += 1
                    tmp = '00{}'.format(counter)
                    serial.serial_number = item.name + tmp[-3:]
            return res

    @api.multi
    def generate_standard_serial(self):
        for item in self:
            serial_ids = []
            for counter in range(item.qty_standard_serial):
                tmp = '00{}'.format(counter + 1)
                serial = item.stock_production_lot_serial_ids.filtered(
                    lambda a: a.serial_number == item.name + tmp[-3:]
                )
                if serial:
                    if not serial.consumed:
                        serial.update({
                            'display_weight': item.standard_weight
                        })
                        serial_ids.append(serial.id)
                else:
                    new_serial = item.env['stock.production.lot.serial'].create({
                        'stock_production_lot_id': item.id,
                        'display_weight': item.standard_weight,
                        'serial_number': item.name + tmp[-3:],
                        'belong_to_prd_lot': True
                    })
                    serial_ids.append(new_serial.id)
            serial_ids += list(item.stock_production_lot_serial_ids.filtered(
                lambda a: a.consumed
            ).mapped('id'))

            item.stock_production_lot_serial_ids = [(6, 0, serial_ids)]

    @api.model
    def get_stock_quant(self):
        return self.quant_ids.filtered(
            lambda a: a.location_id.name == 'Stock'
        )
