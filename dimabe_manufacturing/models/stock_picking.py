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
                if item.lot_search_id:
                    domain = [('id', '=', item.lot_search_id.id)]
                if item.sale_search_id:
                    domain = [('sale_order_id', '=', item.sale_search_id.id)]
                if not item.sale_search_id and not item.lot_search_id:
                    domain = [('product_id.id', '=', item.move_ids_without_package.mapped('product_id').ids),
                              ('available_kg', '>', 0)]
                item.potential_lot_ids = self.env['stock.production.lot'].sudo().search(domain)
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
            res = {
                'domain': {
                    'potential_lot_ids': domain
                }
            }
            return res
