from odoo import fields, models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    stock_picking_id = fields.Many2one('stock.picking', string='Despacho')

    positioning_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('done', 'Listo')
    ], string='Estado movimiento de bodega a producción', default='pending')

    client_id = fields.Many2one('res.partner', string='Cliente', related='stock_picking_id.partner_id')

    destiny_country_id = fields.Many2one('res.country', string='País', related='stock_picking_id.partner_id.country_id')

    charging_mode = fields.Selection(
        related='stock_picking_id.charging_mode',
        string='Modo de carga'
    )

    client_label = fields.Boolean(
        string='Etiqueta cliente',
        related='stock_picking_id.client_label',
    )

    unevenness_percent = fields.Float(
        string='% Descalibre',
    )

    etd = fields.Date(
        string='Fecha de despacho',
        related='stock_picking_id.etd'
    )

    observation = fields.Text('Observación')

    label_durability_id = fields.Many2one(
        'label.durability',
        'Durabilidad etiqueta',
    )

    pt_balance = fields.Float(
        'Saldo bodega pt',
        compute='compute_pt_balance'
    )

    sale_order_id = fields.Many2one('sale.order', string='Pedido de venta', related='stock_picking_id.sale_id')

    consumed_material_ids = fields.One2many('stock.production.lot.serial', 'reserved_to_production_id',
                                            string='Materiales utilizados')

    required_date_moving_to_production = fields.Datetime('Fecha requerida de movimiento a produccion',
                                                         default=fields.Datetime.now())

    requested_qty = fields.Float(
        'Cantidad solicitada'
    )

    material_ids = fields.Many2many('product.product', string='Materiales', compute='compute_material_ids')

    @api.multi
    def compute_pt_balance(self):
        for item in self:
            pt_balance = 0
            if item.stock_picking_id:
                pt_balance = sum(serial.display_weight for serial in item.stock_picking_id.packing_list_ids.filtered(
                    lambda x: x.production_id.id == item.id))
            item.pt_balance = pt_balance

    @api.multi
    def compute_material_ids(self):
        for item in self:
            product_ids = [line.product_id for line in item.bom_id.bom_line_ids]
            if len(product_ids) > 0:
                item.material_ids = product_ids
                return
            item.material_ids = None

    @api.model
    def create(self, values):
        res = super(MrpProduction, self).create(values)
        if res.stock_picking_id:
            res.stock_picking_id.write({
                'has_mrp_production': True
            })
        return res

    def calculate_done(self):
        for item in self:
            production_location_id = self.env['stock.location'].sudo().search([('usage', '=', 'production')], limit=1)
            lot_production_id = item.finished_move_line_ids.filtered(lambda x: x.product_id.id == item.product_id.id)
            if item.product_id.categ_id.parent_id.name == 'Producto Terminado':
                qty_serial_pt = len(self.workorder_ids[0].summary_out_serial_ids.filtered(
                    lambda x: x.product_id.id == item.product_id.id))
                for move in item.move_raw_ids.filtered(lambda x: not x.needs_lots):
                    if len(move.active_move_line_ids) > 0:
                        move.active_move_line_ids.sudo().unlink()
                    component_ids = item.bom_id.bom_line_ids.filtered(lambda x: x.product_id.id == move.product_id.id)
                    self.env['stock.move.line'].sudo().create({
                        'product_id': move.product_id.id,
                        'production_id': item.id,
                        'qty_done': qty_serial_pt / component_ids[0].product_qty,
                        'location_id': item.location_src_id.id,
                        'location_dest_id': production_location_id.id,
                        'move_id': move.id,
                        'state': 'done',
                        'lot_produced_id': lot_production_id.id,
                    })
                    quant_id = self.env['stock.quant'].sudo().search(
                        [('product_id.id', '=', move.product_id.id), ('location_id', '=', item.location_src_id.id)])
                    if quant_id:
                        quant_id.sudo().write({
                            'quantity': quant_id.quantity - qty_serial_pt * component_ids[0].product_qty,
                        })
                        return

    def button_mark_done(self):
        for item in self:
            item.calculate_done()
            final_lot_id = self.finished_move_line_ids.filtered(lambda x: x.product_id.id == item.product_id.id).lot_id
            if len(final_lot_id.temporary_serial_ids) > 0:
                final_lot_id.temporary_serial_ids.sudo().unlink()
            for finished in item.finished_move_line_ids:
                if len(finished.lot_id.stock_production_lot_serial_ids) == 0:
                    finished.sudo().write({
                        'state': 'draft'
                    })
                    finished.sudo().unlink()
                else:
                    finished.sudo().write({
                        'state': 'draft',
                        'qty_done': sum(
                            serial.display_weight for serial in finished.lot_id.stock_production_lot_serial_ids),
                    })
                    finished.lot_id.write({
                        'is_finished': True,
                    })
            res = super(MrpProduction, self).button_mark_done()
            for move in item.move_raw_ids:
                if move.quantity_done == 0 or move.product_uom_qty == 0 or len(move.active_move_line_ids) == 0:
                    move.sudo().write({
                        'state': 'draft'
                    })
                    move.sudo().unlink()
            return res

    def button_plan(self):
        res = super(MrpProduction, self).button_plan()
        for item in self:
            if len(item.workorder_ids) > 0:
                for work_order in item.workorder_ids:
                    for check in work_order.check_ids:
                        if not check.component_is_byproduct:
                            check.qty_done = 0
                            work_order.action_skip()
                        else:
                            if not check.lot_id:
                                lot_tmp = self.env['stock.production.lot'].create({
                                    'name': self.env['ir.sequence'].next_by_code('mrp.workorder'),
                                    'product_id': check.component_id.id,
                                    'is_prd_lot': True
                                })
                                check.lot_id = lot_tmp.id
                                check.qty_done = work_order.component_remaining_qty
                                work_order.active_move_line_ids.filtered(lambda a: a.lot_id.id == lot_tmp.id).write({
                                    'is_raw': False
                                })
                                if check.quality_state == 'none' and check.qty_done > 0:
                                    work_order.action_next()
                            else:
                                work_order.active_move_line_ids.filtered(
                                    lambda a: a.lot_id.id == check.lot_id.id).write({
                                    'is_raw': False
                                })
                    work_order.action_first_skipped_step()
        return res

    def update_stock_move(self):
        for item in self:
            production_location_id = self.env['stock.location'].sudo().search([('usage', '=', 'production')], limit=1)
            for bom_line in item.bom_id.bom_line_ids:
                if bom_line.product_id not in item.move_raw_ids.mapped('product_id'):
                    qty = (item.product_qty / item.bom_id.product_qty) * bom_line.product_qty
                    stock_move = self.env['stock.move'].sudo().create({
                        'product_id': bom_line.product_id.id,
                        'product_uom': bom_line.product_uom_id.id,
                        'location_id': item.location_src_id.id,
                        'product_uom_qty': qty,
                        'location_dest_id': production_location_id.id,
                        'company_id': self.company_id.id,
                        'date': fields.Date.today(),
                        'name': f'Nuevo material {bom_line.product_id.display_name}',
                        'raw_material_production_id': item.id,
                    })
                    if len(item.workorder_ids) > 0:
                        if stock_move.needs_lots:
                            workorder_id = item.workorder_ids[0]
                            self.env['stock.move.line'].sudo().create({
                                'product_id': bom_line.product_id.id,
                                'product_uom_id': bom_line.product_uom_id.id,
                                'product_uom_qty': qty,
                                'location_id': item.location_src_id.id,
                                'location_dest_id': production_location_id.id,
                                'workorder_id': workorder_id.id,
                                'move_id': stock_move.id,
                                'state': 'confirmed',
                                'done_wo': False,
                            })
