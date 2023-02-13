from odoo import models, api, fields
from odoo.addons import decimal_precision as dp


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    has_mrp_production = fields.Boolean('Tiene orden de production')

    country_id = fields.Many2one('res.country', string="Pais", related='partner_id.country_id')

    quantity_requested = fields.Float(
        string="Demanda",
        related="move_ids_without_package.product_uom_qty",
        digits=dp.get_precision('Product Unit of Measure'))

    variety = fields.Many2many(string="Atributos", related='product_id.attribute_value_ids')

    product_id = fields.Many2one(string="Producto")

    product_ids = fields.Many2many('product.product', string="Productos", compute='compute_product_ids')

    real_net_weigth = fields.Float('Kilos Netos Reales', compute='compute_net_weigth_real')

    # Packing List Info

    packing_list_ids = fields.One2many(
        'stock.production.lot.serial',
        'reserved_to_stock_picking_id',
        string='Packing List (Series)')

    potential_lot_ids = fields.Many2many(
        'stock.production.lot',
        compute='compute_potential_lot',
        string='Lotes a reservar'
    )

    assigned_pallet_ids = fields.One2many(
        'manufacturing.pallet',
        'reserved_to_stock_picking_id',
        string='Pallets reservados'
    )

    packing_list_lot_ids = fields.Many2many(
        'stock.production.lot',
        compute='compute_packing_list_lot'
    )

    # Filter for reserved

    sale_search_id = fields.Many2one(
        'sale.order',
        'Pedido',
        copy=False)

    lot_search_id = fields.Many2one(
        'stock.production.lot',
        string='Lote a buscar',
        copy=False
    )

    # Multiple Dispatch

    is_multiple_dispatch = fields.Boolean('Es despacho multiple?', copy=False)

    sale_order_ids = fields.Many2one(
        'sale.order',
        string='Pedido',
        domain=[('state', '=', 'sale')], copy=False)

    dispatch_id = fields.Many2one(
        'stock.picking',
        string='Despachos',
        domain=[('state', '!=', 'done')],
        copy=False)

    dispatch_line_ids = fields.One2many(
        'custom.dispatch.line',
        'dispatch_real_id',
        copy=False,
        string='Despachos')

    picking_real_id = fields.Many2one(
        'stock.picking',
        string='Despacho Real',
        copy=False
    )

    picking_principal_id = fields.Many2one(
        'stock.picking',
        string='Despacho Principal',
        copy=False
    )

    is_child_dispatch = fields.Boolean('Es despacho hijo', copy=False)

    name_orders = fields.Char('Nombre de pedidos', compute='compute_name_orders')

    # Compute Methods

    @api.depends('lot_search_id', 'sale_search_id')
    @api.multi
    def compute_potential_lot(self):
        for item in self:
            if item.picking_type_code == 'outgoing':
                domain = [('product_id.id', '=', item.move_ids_without_package.mapped('product_id').ids),
                          ('available_kg', '>', 0)]
                if item.lot_search_id:
                    domain = [('id', '=', item.lot_search_id.id)]
                if item.sale_search_id:
                    domain = [('sale_order_id', '=', item.sale_search_id.id)]
                lot_ids = self.env['stock.production.lot'].sudo().search(domain).filtered(lambda x: any(
                    not serial.reserved_to_stock_picking_id for serial in x.stock_production_lot_serial_ids))
                item.potential_lot_ids = lot_ids
                return
            item.potential_lot_ids = None

    @api.multi
    def compute_packing_list_lot(self):
        for item in self:
            if item.picking_type_code == 'outgoing':
                if item.packing_list_ids:
                    item.packing_list_lot_ids = item.packing_list_ids.mapped('stock_production_lot_id')
                    return
            item.packing_list_lot_ids = None

    @api.multi
    def compute_name_orders(self):
        for item in self:
            if item.is_multiple_dispatch:
                item.name_orders = ','.join([line.sale_id.name for line in item.dispatch_line_ids])
                return
            item.name_orders = ''

    @api.multi
    def compute_product_ids(self):
        for item in self:
            if item.move_ids_without_package:
                item.product_ids = item.move_ids_without_package.mapped('product_id')
                return
            item.product_ids = None

    @api.multi
    def compute_net_weigth_real(self):
        for item in self:
            item.real_net_weigth = sum(item.packing_list_ids.mapped('display_weight'))

    # Onchange method
    @api.onchange('is_multiple_dispatch')
    def set_multiple_dispatch(self):
        if self.is_multiple_dispatch and self.move_ids_without_package:
            # Se busca objecto a causa de que self.id entrega otro tipo de campo (NewId)
            picking = self.env['stock.picking'].search([('name', '=', self.name)])
            if picking:
                self.env['custom.dispatch.line'].create({
                    'dispatch_real_id': picking.id,
                    'dispatch_id': picking.id,
                    'product_id': self.move_ids_without_package.mapped('product_id').id if len(
                        self.move_ids_without_package) == 1 else self.move_ids_without_package[0].mapped(
                        'product_id').id,
                    'required_sale_qty': self.move_ids_without_package.product_uom_qty if len(
                        self.move_ids_without_package) == 1 else self.move_ids_without_package[0].product_uom_qty,
                    'sale_id': self.sale_id.id
                })

    @api.onchange('picking_type_id')
    def on_change_picking_type(self):
        for item in self:
            if item.picking_type_id.code == 'incoming':
                domain = [('is_company', '=', True), ('supplier', '=', True), ('name', '!=', ''),
                          ('type', '=', 'contact'), ('parent_id', '=', False)]
            if item.picking_type_id.code == 'outgoing':
                domain = [('is_company', '=', True), ('customer', '=', True), ('name', '!=', ''),
                          ('type', '=', 'contact'), ('parent_id', '=', False)]
            res = {
                'domain': {
                    'partner_id': domain
                }
            }
            return res

    @api.onchange('lot_search_id')
    def on_change_lot_search_id(self):
        for item in self:
            if item.lot_search_id:
                domain = [('id', '=', item.lot_search_id.id)]
            else:
                domain = [('product_id.id', '=', item.move_ids_without_package.mapped('product_id').ids),
                 ('available_kg', '>', 0)]
            res = {
                'domain': {
                    'potential_lot_ids': domain
                }
            }
            return res

    # Action Methods

    @api.multi
    def action_cancel(self):
        for item in self:
            lot = self.env['stock.production.lot'].search([('name', '=', item.name)])
            if lot:
                quant = self.env['stock.quant'].sudo().search([('lot_id.id', '=', lot.id)])
                if quant:
                    quant.sudo().unlink()
                lot.stock_production_lot_serial_ids.sudo().unlink()
                lot.sudo().unlink()
            return super(StockPicking, self).action_cancel()

    @api.multi
    def calculate_last_serial(self):
        if self.picking_type_code == 'incoming':
            if len(canning) == 1:
                if self.production_net_weight == self.net_weight:
                    self.production_net_weight = self.net_weight - self.quality_weight

                self.env['stock.production.lot.serial'].search([('stock_production_lot_id', '=', self.name)]).write({
                    'real_weight': self.avg_unitary_weight
                })
                diff = self.production_net_weight - (canning.product_uom_qty * self.avg_unitary_weight)
                self.env['stock.production.lot.serial'].search([('stock_production_lot_id', '=', self.name)])[-1].write(
                    {
                        'real_weight': self.avg_unitary_weight + diff
                    })

    @api.multi
    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        for stock_picking in self:
            mp_move = stock_picking.get_mp_move()
            if stock_picking.picking_type_id.require_dried:
                for move_line in mp_move.move_line_ids:
                    move_line.lot_id.unpelled_state = 'draft'
            mp_move.move_line_ids.mapped('lot_id').write({
                'stock_picking_id': stock_picking.id
            })
            for lot_id in mp_move.move_line_ids.mapped('lot_id'):
                if lot_id.stock_production_lot_serial_ids:
                    lot_id.stock_production_lot_serial_ids.write({
                        'producer_id': lot_id.stock_picking_id.partner_id.id
                    })
        return res

    def validate_barcode(self, barcode):
        custom_serial = self.packing_list_ids.filtered(
            lambda a: a.serial_number == barcode
        )
        if not custom_serial:
            raise models.ValidationError('el código {} no corresponde a este despacho'.format(barcode))
        return custom_serial

    def on_barcode_scanned(self, barcode):
        for item in self:
            custom_serial = item.validate_barcode(barcode)
            if custom_serial.consumed:
                raise models.ValidationError('el código {} ya fue consumido'.format(barcode))

            stock_move_line = self.move_line_ids_without_package.filtered(
                lambda a: a.product_id == custom_serial.stock_production_lot_id.product_id and
                          a.lot_id == custom_serial.stock_production_lot_id and
                          a.product_uom_qty == custom_serial.display_weight and
                          a.qty_done == 0
            )

            if len(stock_move_line) > 1:
                stock_move_line[0].write({
                    'qty_done': custom_serial.display_weight
                })
            else:
                stock_move_line.write({
                    'qty_done': custom_serial.display_weight
                })

            custom_serial.sudo().write({
                'consumed': True
            })

    @api.multi
    def remove_reserved_pallet(self):
        lots = self.assigned_pallet_ids.filtered(lambda a: a.remove_picking).mapped('lot_id')
        pallets = self.assigned_pallet_ids.filtered(
            lambda a: a.remove_picking and a.reserved_to_stock_picking_id.id == self.id)
        for pallet in pallets:
            pallet.lot_serial_ids.filtered(lambda a: a.reserved_to_stock_picking_id.id == self.id).write({
                'reserved_to_stock_picking_id': None
            })
            pallet.write({
                'reserved_to_stock_picking_id': None,
                'remove_picking': False
            })
        self.update_move(lots)

    def update_move(self, lots):
        for lot in lots:
            move = self.move_line_ids_without_package.filtered(lambda a: a.lot_id.id == lot.id)
            if move:
                if lot.get_reserved_quantity_by_picking(self.id) > 0:
                    move.write({
                        'product_uom_qty': lot.get_reserved_quantity_by_picking(self.id)
                    })
                else:
                    move.unlink()
                self.dispatch_line_ids.filtered(lambda a: a.product_id.id == lot.product_id.id).mapped(
                    'move_line_ids').filtered(lambda a: a.lot_id.id == lot.id).write({
                    'product_uom_qty': lot.get_reserved_quantity_by_picking(self.id)
                })
                self.dispatch_line_ids.filtered(
                    lambda a: a.product_id.id == lot.product_id.id and lot in a.move_line_ids.mapped('lot_id')).write({
                    'real_dispatch_qty': sum(
                        self.packing_list_ids.filtered(lambda a: a.stock_production_lot_id == lot).mapped(
                            'display_weight'))
                })

    @api.multi
    def _compute_packing_list_lot_ids(self):
        for item in self:
            if item.packing_list_ids and item.picking_type_code == 'outgoing':
                item.packing_list_lot_ids = item.packing_list_ids.mapped('stock_production_lot_id')
            else:
                item.packing_list_lot_ids = []

    @api.multi
    def remove_reserved_serial(self):
        lots = self.packing_list_ids.filtered(lambda a: a.to_delete).mapped('stock_production_lot_id')
        self.packing_list_ids.filtered(lambda a: a.to_delete and a.reserved_to_stock_picking_id.id == self.id).write({
            'reserved_to_stock_picking_id': None,
            'to_delete': False
        })
        self.update_move(lots)

    @api.multi
    def add_orders_to_dispatch(self):
        if self.is_multiple_dispatch:
            if not self.sale_orders_id:
                raise models.ValidationError('No se selecciono ningun numero de pedido')
            if not self.dispatch_id:
                raise models.ValidationError('No se selecciono ningun despacho')
            if self.dispatch_id in self.dispatch_line_ids.mapped('dispatch_id'):
                raise models.ValidationError('El despacho {} ya se encuentra agregado'.format(self.dispatch_id.id))
            for product in self.dispatch_id.move_ids_without_package:
                self.env['custom.dispatch.line'].create({
                    'dispatch_real_id': self.id,
                    'dispatch_id': self.dispatch_id.id,
                    'sale_id': self.sale_orders_id.id,
                    'product_id': product.product_id.id,
                    'required_sale_qty': product.product_uom_qty,
                })
                # No existe producto
                if not self.move_ids_without_package.filtered(lambda p: p.product_id.id == product.product_id.id):
                    self.env['stock.move'].create({
                        'product_id': product.product_id.id,
                        'picking_id': self.id,
                        'product_uom': product.product_id.uom_id.id,
                        'product_uom_qty': product.product_uom_qty,
                        'date': datetime.date.today(),
                        'date_expected': self.scheduled_date,
                        'location_dest_id': self.partner_id.property_stock_customer.id,
                        'location_id': self.location_id.id,
                        'name': product.product_id.name,
                        'procure_method': 'make_to_stock',
                    })
                else:
                    move = self.move_ids_without_package.filtered(lambda p: p.product_id.id == product.product_id.id)
                    move.write({
                        'product_uom_qty': move.product_uom_qty + product.product_uom_qty
                    })
