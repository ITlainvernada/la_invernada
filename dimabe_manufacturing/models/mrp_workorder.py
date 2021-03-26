from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
from datetime import date, datetime


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    show_manual_input = fields.Boolean(
        'Digitar Serie Manualmente'
    )

    positioning_state = fields.Selection(
        related='production_id.positioning_state',
        string='Estado movimiento de bodega a producción'
    )

    client_id = fields.Many2one(
        'res.partner',
        related='production_id.client_id',
        string='Cliente',
        store=True
    )

    destiny_country_id = fields.Many2one(
        'res.country',
        related='production_id.destiny_country_id',
        string='País',
        store=True
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        related='production_id.stock_picking_id.sale_id',
        string='Pedido de Venta',
        store=True
    )

    pt_balance = fields.Float(
        'Saldo Bodega PT',
        digits=dp.get_precision('Product Unit of Measure'),
        related='production_id.pt_balance'
    )

    charging_mode = fields.Selection(
        related='production_id.charging_mode',
        string='Modo de Carga'
    )

    client_label = fields.Boolean(
        'Etiqueta Cliente',
        related='production_id.client_label'
    )

    unevenness_percent = fields.Float(
        '% Descalibre',
        digits=dp.get_precision('Product Unit of Measure'),
        related='production_id.unevenness_percent'
    )

    etd = fields.Date(
        'Fecha de Despacho',
        related='production_id.etd'
    )

    label_durability_id = fields.Many2one(
        'label.durability',
        string='Durabilidad Etiqueta',
        related='production_id.label_durability_id'
    )

    observation = fields.Text(
        'Observación',
        related='production_id.observation'
    )

    production_finished_move_line_ids = fields.One2many(
        string='Productos Finalizados',
        related='production_id.finished_move_line_ids'
    )

    summary_out_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_summary_out_serial_ids',
        string='Resumen de Salidas'
    )

    material_product_ids = fields.One2many(
        'product.product',
        compute='_compute_material_product_ids'
    )

    byproduct_move_line_ids = fields.One2many(
        'stock.move.line',
        compute='_compute_byproduct_move_line_ids',
        string='subproductos'
    )

    potential_serial_planned_ids = fields.One2many(
        'stock.production.lot.serial',
        'used_in_workorder_id'
    )

    confirmed_serial = fields.Char('Codigo de Barra')

    manufacturing_pallet_ids = fields.One2many(
        'manufacturing.pallet',
        compute='_compute_manufacturing_pallet_ids',
        string='Pallets'
    )

    there_is_serial_without_pallet = fields.Boolean(
        'Hay Series sin pallet',
        compute='_compute_there_is_serial_without_pallet'
    )

    is_match = fields.Boolean('Es Partido', compute='compute_is_match')

    product_variety = fields.Char(related='product_id.variety')

    location_id = fields.Many2one('stock.location', related='production_id.location_dest_id')

    product_qty = fields.Float(related='production_id.product_qty')

    lot_produced_id = fields.Integer('Lote a producir', compute='_compute_lot_produced')

    in_weight = fields.Float('Kilos Ingresados',
                             digits=dp.get_precision('Product Unit of Measure'), store=True)

    out_weight = fields.Float('Kilos Producidos', compute='_compute_out_weight',
                              digits=dp.get_precision('Product Unit of Measure'), store=True)

    pt_out_weight = fields.Float('Kilos Producidos del PT', compute='_compute_pt_out_weight',
                                 digits=dp.get_precision('Product Unit of Meausure'), store=True)

    producers_id = fields.Many2many('res.partner', string='Productores')

    producer_to_view = fields.Many2many('res.partner', string='Productores', compute='_compute_producers_id')

    pallet_qty = fields.Integer('Cantidad de Pallets', compute='_compute_pallet_qty')

    pallet_content = fields.Float('Kilos Totales', compute='_compute_pallet_content')

    pallet_serial = fields.Integer('Total de Series', compute='_compute_pallet_serial')

    have_subproduct = fields.Boolean('Tiene subproductos')

    component_id = fields.Many2one('product.product', readonly=False)

    to_done = fields.Boolean('Para Finalizar')

    @api.multi
    def _compute_producers_id(self):
        for item in self:
            if item.potential_serial_planned_ids and item.state == 'done' and not item.producers_id:
                item.producer_to_view = item.potential_serial_planned_ids.mapped('producer_id')
            elif item.potential_serial_planned_ids and item.state != 'done' and item.producers_id:
                item.producer_to_view = item.producer_to_view

    @api.multi
    def fix_env(self):
        workorder_ids = self.env['mrp.workorder'].search([])
        for work in workorder_ids:
            first_state = work.state
            if first_state == 'done':
                query = f"UPDATE mrp_workorder set state = 'ready' where id = {work.id}"
                cr = self._cr
                cr.execute(query)
            producer_ids = self.env['stock.production.lot.serial'].search(
                [('used_in_workorder_id.id', '=', work.id)]).mapped('producer_id')
            for prod in producer_ids:
                work.write({
                    'producer_ids': [(4, prod.id)]
                })
            if first_state == 'done':
                query = f"UPDATE mrp_workorder set state = 'done' where id = {work.id}"
                cr = self._cr
                cr.execute(query)

    @api.multi
    def _compute_pallet_content(self):
        for item in self:
            if item.manufacturing_pallet_ids:
                item.pallet_content = sum(item.manufacturing_pallet_ids.mapped('total_content_weight'))

    @api.multi
    def _compute_pallet_serial(self):
        for item in self:
            if item.manufacturing_pallet_ids:
                item.pallet_serial = len(item.manufacturing_pallet_ids.mapped('lot_serial_ids'))

    @api.multi
    def _compute_pallet_qty(self):
        for item in self:
            if item.manufacturing_pallet_ids:
                item.pallet_qty = len(item.manufacturing_pallet_ids)

    @api.depends('summary_out_serial_ids')
    @api.multi
    def _compute_out_weight(self):
        for item in self:
            if item.summary_out_serial_ids:
                item.out_weight = sum(item.summary_out_serial_ids.mapped('real_weight'))

    @api.depends('summary_out_serial_ids')
    @api.multi
    def _compute_pt_out_weight(self):
        for item in self:
            if item.summary_out_serial_ids:
                item.pt_out_weight = sum(
                    item.summary_out_serial_ids.filtered(lambda a: 'PT' in a.product_id.default_code).mapped(
                        'real_weight'))

    @api.multi
    def show_in_serials(self):
        self.ensure_one()
        return {
            'name': "Series de Entrada",
            'view_type': 'form',
            'view_mode': 'tree,graph,form,pivot',
            'res_model': 'stock.production.lot.serial',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'views': [
                [self.env.ref('dimabe_manufacturing.stock_production_lot_serial_process_in_form_view').id, 'tree']],
            'context': self.env.context,
            'domain': [('id', 'in', self.potential_serial_planned_ids.mapped("id"))]
        }

    @api.multi
    def show_out_serials(self):
        self.ensure_one()
        return {
            'name': "Series de Salida",
            'view_type': 'form',
            'view_mode': 'tree,graph,form,pivot',
            'res_model': 'stock.production.lot.serial',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'views': [
                [self.env.ref('dimabe_manufacturing.stock_production_lot_serial_process_out_form_view').id, 'tree']],
            'context': self.env.context,
            'domain': [('id', 'in', self.summary_out_serial_ids.mapped("id"))]
        }

    @api.multi
    def _compute_lot_produced(self):
        for item in self:
            if len(item.production_finished_move_line_ids) > 1:
                item.lot_produced_id = item.production_finished_move_line_ids.filtered(
                    lambda a: a.product_id == item.product_id.id).lot_id.id
            item.lot_produced_id = item.final_lot_id.id

    @api.multi
    def compute_is_match(self):
        for item in self:
            item.is_match = item.production_id.routing_id.code == 'RO/00006'

    @api.multi
    def _compute_there_is_serial_without_pallet(self):
        for item in self:
            if item.summary_out_serial_ids:
                item.there_is_serial_without_pallet = len(item.summary_out_serial_ids.filtered(
                    lambda a: not a.pallet_id)) > 0

    @api.multi
    def _compute_manufacturing_pallet_ids(self):
        for item in self:
            if item.summary_out_serial_ids:
                pallet_ids = []
                for pallet_id in item.summary_out_serial_ids.mapped('pallet_id'):
                    if pallet_id.id not in pallet_ids:
                        pallet_ids.append(pallet_id.id)
                if pallet_ids:
                    item.manufacturing_pallet_ids = [(4, pallet_id) for pallet_id in pallet_ids]

    @api.onchange('qty_producing')
    def _onchange_qty_producing(self):
        print('se inhabilita este método')

    @api.multi
    def _compute_summary_out_serial_ids(self):
        for item in self:
            if item.final_lot_id:
                item.summary_out_serial_ids = item.final_lot_id.stock_production_lot_serial_ids
                if item.byproduct_move_line_ids:
                    item.summary_out_serial_ids += item.byproduct_move_line_ids.filtered(
                        lambda a: a.lot_id not in item.potential_serial_planned_ids.mapped(
                            'stock_production_lot_id')).mapped(
                        'lot_id'
                    ).mapped(
                        'stock_production_lot_serial_ids'
                    )
            else:
                item.summary_out_serial_ids = item.production_finished_move_line_ids.filtered(
                    lambda a: a.lot_id not in item.potential_serial_planned_ids.mapped(
                        'stock_production_lot_id')).mapped(
                    'lot_id'
                ).mapped(
                    'stock_production_lot_serial_ids'
                )

    @api.multi
    def _compute_byproduct_move_line_ids(self):
        for item in self:
            if not item.byproduct_move_line_ids:
                item.byproduct_move_line_ids = item.active_move_line_ids.filtered(lambda a: not a.is_raw)

    @api.multi
    def _compute_material_product_ids(self):
        for item in self:
            if not item.material_product_ids:
                item.material_product_ids = item.production_id.move_raw_ids.mapped('product_id')

    @api.model
    def create(self, values_list):
        res = super(MrpWorkorder, self).create(values_list)

        name = self.env['ir.sequence'].next_by_code('mrp.workorder')

        final_lot = self.env['stock.production.lot'].create({
            'name': name,
            'product_id': res.product_id.id,
            'is_prd_lot': True,
            'can_add_serial': True,
            'label_durability_id': res.production_id.label_durability_id.id
        })
        res.final_lot_id = final_lot.id
        return res

    @api.multi
    def write(self, vals):
        for item in self:
            if item.active_move_line_ids and \
                    not item.active_move_line_ids.filtered(lambda a: a.is_raw):
                for move_line in item.active_move_line_ids:
                    move_line.update({
                        'is_raw': True
                    })
        res = super(MrpWorkorder, self).write(vals)
        return res

    def open_tablet_view(self):
        for check in self.check_ids:
            if not check.component_is_byproduct:
                check.qty_done = 0
                self.action_skip()
            else:
                if not check.lot_id:
                    lot_tmp = self.env['stock.production.lot'].create({
                        'name': self.env['ir.sequence'].next_by_code('mrp.workorder'),
                        'product_id': check.component_id.id,
                        'is_prd_lot': True
                    })
                    check.lot_id = lot_tmp.id
                    check.qty_done = self.component_remaining_qty
                    self.active_move_line_ids.filtered(lambda a: a.lot_id.id == lot_tmp.id).write({
                        'is_raw': False
                    })
                    if check.quality_state == 'none' and check.qty_done > 0:
                        self.action_next()
        self.action_first_skipped_step()
        return super(MrpWorkorder, self).open_tablet_view()

    def new_screen_in(self):
        for check in self.check_ids:
            if not check.component_is_byproduct:
                check.qty_done = 0
                self.action_skip()
            else:
                if not check.lot_id:
                    lot_tmp = self.env['stock.production.lot'].create({
                        'name': self.env['ir.sequence'].next_by_code('mrp.workorder'),
                        'product_id': check.component_id.id,
                        'is_prd_lot': True
                    })
                    check.lot_id = lot_tmp.id
                    check.qty_done = self.component_remaining_qty
                    self.active_move_line_ids.filtered(lambda a: a.lot_id.id == lot_tmp.id).write({
                        'is_raw': False
                    })
                    if check.quality_state == 'none' and check.qty_done > 0:
                        self.action_next()
        self.action_first_skipped_step()
        return {
            'name': "Procesar Entrada",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.workorder',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'views': [
                [self.env.ref('dimabe_manufacturing.mrp_workorder_process_view').id, 'form']],
            'res_id': self.id,
        }

    def do_finish(self):
        self.write({
            'lot_produced_id': self.final_lot_id.id
        })
        if self.production_id.move_raw_ids.filtered(lambda a: not a.product_uom):
            raise models.ValidationError(
                '{}'.format(self.production_id.move_raw_ids.filtered(lambda a: not a.product_uom)))
        super(MrpWorkorder, self).do_finish()
        self.organize_move_line()

    def action_skip(self):
        self.write({
            'in_weight': sum(self.potential_serial_planned_ids.mapped('real_weight'))
        })
        super(MrpWorkorder, self).action_skip()

    def action_ignore(self):
        for move in self.active_move_line_ids:
            if not move.lot_id:
                move.unlink()
        self.action_skip()
        for skip in self.skipped_check_ids:
            skip.unlink()


    def confirmed_serial_keyboard(self):
        self.ensure_one()
        qty_done = self.qty_done
        custom_serial = self.validate_serial_code(self.confirmed_serial)
        custom_serial.write({
            'reserved_to_production_id': self.production_id.id,
            'consumed': True
        })
        lot = self.env['stock.production.lot'].search([('name', '=', custom_serial.stock_production_lot_id.name)])
        available_kg = sum(lot.stock_production_lot_serial_ids.filtered(lambda a: not a.consumed).mapped('real_weight'))
        lot.write({
            'available_kg': available_kg
        })
        if custom_serial:
            barcode = custom_serial.stock_production_lot_id.name
        res = super(MrpWorkorder, self).on_barcode_scanned(self.confirmed_serial)
        if res:
            return res
        self.qty_done = qty_done + custom_serial.display_weight
        self.write({
            'in_weight': sum(self.potential_serial_planned_ids.mapped('real_weight')),
            'lot_id': custom_serial.stock_production_lot_id.id
        })
        quant = self.env['stock.quant'].search([('lot_id', '=', lot.id)])
        quant.write({
            'quantity': sum(
                lot.stock_production_lot_serial_ids.filtered(lambda a: not a.consumed).mapped('real_weight'))
        })
        return res

    @api.onchange('confirmed_serial')
    def confirmed_keyboard(self):
        self.process_serial(self.confirmed_serial)

    def process_serial(self, serial_number):
        raise models.ValdidationError(f'{self._origin.production_id}')
        serial_number = serial_number.strip()
        serial = self.env['stock.production.lot.serial'].search([('serial_number', '=', serial_number)])
        if not serial:
            raise models.ValidationError(f'La serie ingresada no existe')
        if serial.product_id not in self.material_product_ids:
            raise models.UserError(
                f'El producto de la serie {serial.serial_number} no es compatible con la lista de materiales')
        if serial.consumed:
            raise models.UserError(
                f'El serie se encuentra consumida en el proceso {serial.reserved_to_production_id.name}')
        self.component_id = serial.product_id
        self.write({
            'lot_id': serial.stock_production_lot_id.id,
            'in_weight': sum(self.potential_serial_planned_ids.mapped('display_weight'))
        })
        serial.write({
            'reserved_to_production_id': self.production_id.id,
            'consumed': True
        })
        serial.stock_production_lot_id.update_stock_quant(self.production_id.location_src_id.id)
        serial.stock_production_lot_id.update_kg(serial.stock_production_lot_id.id)
        line_new = self.env['stock.move.line']
        move = self.production_id.move_raw_ids.filtered(lambda a: a.product_id.id == serial.product_id.id)
        if move.active_move_line_ids:
            line = move.active_move_line_ids.filtered(lambda a: a.lot_id == serial.stock_production_lot_id)
            if not line.lot_produced_id:
                line.write({
                    'lot_produced_id': self.final_lot_id.id
                })
            line.write({
                'qty_done': sum(self.potential_serial_planned_ids.filtered(
                    lambda a: a.stock_production_lot_id.id == serial.stock_production_lot_id.id).mapped(
                    'display_weight'))
            })
        else:
            line_new = self.env['stock.move.line'].create({
                'lot_id': serial.stock_production_lot_id.id,
                'lot_produced_id': self.final_lot_id.id,
                'product_id': move.product_id.id,
                'location_dest_id': self.env['stock.location'].search([('usage', '=', 'production')]).id,
                'location_id': self.production_id.location_src_id.id,
                'move_id': move.id,
                'product_uom_id': serial.product_id.uom_id.id,
                'date': date.today(),
                'qty_done': sum(self.potential_serial_planned_ids.filtered(
                    lambda a: a.stock_production_lot_id.id == serial.stock_production_lot_id.id).mapped(
                    'display_weight')),
                'production_id': self.production_id.id,
                'workorder_id': self.id
            })
        if self.active_move_line_ids.filtered(lambda a: not a.lot_id and a.product_id.id == serial.product_id.id):
            line_wo = self.active_move_line_ids.filtered(
                lambda a: not a.lot_id and a.product_id.id == serial.product_id.id)
            line_wo.write({
                'lot_id': serial.stock_production_lot_id.id,
                'qty_done': sum(self.potential_serial_planned_ids.filtered(
                    lambda a: a.stock_production_lot_id.id == serial.stock_production_lot_id.id).mapped(
                    'display_weight'))
            })
        else:
            line_wo = self.active_move_line_ids.filtered(
                lambda a: a.lot_id.id == serial.stock_production_lot_id.id and a.product_id.id == serial.product_id.id)
            if line_wo:
                line_wo.write({
                    'qty_done': sum(self.potential_serial_planned_ids.filtered(
                        lambda a: a.stock_production_lot_id.id == serial.stock_production_lot_id.id).mapped(
                        'display_weight'))
                })
            else:
                self.env['stock.move.line'].create({
                    'lot_id': serial.stock_production_lot_id.id,
                    'lot_produced_id': self.final_lot_id.id,
                    'product_id': move.product_id.id,
                    'location_dest_id': self.env['stock.location'].search([('usage', '=', 'production')]).id,
                    'location_id': self.production_id.location_src_id.id,
                    'move_id': self.move_raw_ids.filtered(lambda a: a.product_id.id == serial.product_id.id).id,
                    'product_uom_id': serial.product_id.uom_id.id,
                    'date': date.today(),
                    'qty_done': sum(self.potential_serial_planned_ids.filtered(
                        lambda a: a.stock_production_lot_id.id == serial.stock_production_lot_id.id).mapped(
                        'display_weight')),
                    'production_id': self.production_id.id,
                    'workorder_id': self.id,
                    'done_wo': False
                })
        check = self.check_ids.filtered(
            lambda a: a.component_id.id == serial.product_id.id and not a.component_is_byproduct)
        check.write({
            'lot_id': serial.stock_production_lot_id.id,
            'move_line_id': line_new.id if line_new.id else line.id,
            'qty_done': sum(
                self.potential_serial_planned_ids.filtered(lambda a: a.product_id.id == serial.product_id.id).mapped(
                    'display_weight'))
        })
        if check.quality_state != 'pass':
            check.do_pass()
        self.write({
            'confirmed_serial': None,
            'current_quality_check_id': check.id
        })

    def on_barcode_scanned(self, barcode):
        self.process_serial(barcode)
        return super(MrpWorkorder, self).on_barcode_scanned(barcode)

    @api.multi
    def validate_to_done(self):
        for check in self.check_ids.filtered(
                lambda a: (not a.component_is_byproduct and a.quality_state != 'pass') or not a.lot_id):
            check.unlink()
        for move in self.active_move_line_ids.filtered(lambda a: not a.lot_id):
            move.unlink()
        self.write({
            'to_done': True
        })

    @api.model
    def lot_is_byproduct(self):
        return self.finished_product_check_ids.filtered(
            lambda a: a.lot_id == self.lot_id and a.component_is_byproduct
        )

    def validate_serial_code(self, barcode):
        custom_serial = self.env['stock.production.lot.serial'].search(
            [('serial_number', '=', barcode)])
        if custom_serial:
            if custom_serial.product_id != self.component_id:
                raise models.ValidationError('El producto ingresado no corresponde al producto solicitado')
            if custom_serial.consumed:
                raise models.ValidationError('este código ya ha sido consumido en la produccion {}'.format(
                    custom_serial.reserved_to_production_id.name))
            return custom_serial
        return custom_serial

    def open_out_form_view(self):
        for item in self:
            item.write({
                'out_weight': sum(item.summary_out_serial_ids.mapped('real_weight')),
                'pt_out_weight': sum(
                    item.summary_out_serial_ids.filtered(lambda a: a.product_id.id == self.product_id.id).mapped(
                        'real_weight'))
            })
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.workorder',
                'views': [[self.env.ref('dimabe_manufacturing.mrp_workorder_out_form_view').id, 'form']],
                'res_id': self.id,
                'target': 'fullscreen'
            }

    def create_pallet(self):
        default_product_id = None
        if 'default_product_id' in self.env.context:
            default_product_id = self.env.context['default_product_id']
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'manufacturing.pallet',
            'views': [[self.env.ref('dimabe_manufacturing.manufacturing_pallet_form_view').id, 'form']],
            'target': 'fullscreen',
            'context': {'_default_product_id': default_product_id}
        }

    def update_inventory(self, lot_name):
        lot = self.env['stock.production.lot'].search([('name', '=', lot_name)])
        lot.write({
            'available_kg': sum(lot.stock_production_lot_serial_ids.mapped('real_weight'))
        })
        self.write({
            'in_weight': sum(self.potential_serial_planned_ids.mapped('real_weight'))
        })
        quant = self.env['stock.quant'].search([('lot_id', '=', lot.id)])
        quant.write({
            'quantity': sum(lot.stock_production_lot_serial_ids.mapped('real_weight'))
        })
