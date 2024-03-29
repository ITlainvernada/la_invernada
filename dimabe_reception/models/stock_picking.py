import json
from datetime import datetime, date

import requests

from odoo import models, api, fields
from odoo.addons import decimal_precision as dp


import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'date desc'

    guide_number = fields.Integer('Número de Guía')

    weight_guide = fields.Float(
        'Kilos Guía',
        compute='_compute_weight_guide',
        store=True,
        track_visibility='onchange',
        digits=dp.get_precision('Product Unit of Measure')
    )

    gross_weight = fields.Float(
        'Kilos Brutos (Recepcion)',
        track_visibility='onchange',
        digits=dp.get_precision('Product Unit of Measure')
    )

    tare_weight = fields.Float(
        'Peso Tara',
        track_visibility='onchange',
        digits=dp.get_precision('Product Unit of Measure')
    )

    net_weight = fields.Float(
        'Kilos Netos',
        compute='_compute_net_weight',
        store=True,
        track_visibility='onchange',
        default=lambda self: self.move_ids_without_package[0].product_uom_qty if self.is_return and len(
            self.move_ids_without_package) > 0 else 0,
        digits=dp.get_precision('Product Unit of Measure')
    )

    canning_weight = fields.Float(
        'Peso Envases',
        compute='_compute_canning_weight',
        track_visibility='onchange',
        store=True,
        digits=dp.get_precision('Product Unit of Measure')
    )

    production_net_weight = fields.Float(
        'Kilos Netos Producción',
        compute='_compute_production_net_weight',
        track_visibility='onchange',
        store=True,
        digits=dp.get_precision('Product Unit of Measure')
    )

    # reception_type_selection = fields.Selection([
    #     ('ins', 'Insumos'),
    #     ('mp', 'Materia Prima')
    # ],
    #     default='ins',
    #     string='Tipo de recepción'
    # )

    is_mp_reception = fields.Boolean(
        'Recepción de MP',
        compute='_compute_is_mp_reception',
        store=True
    )

    is_pt_reception = fields.Boolean(
        'Recepción de PT',
        compute='_compute_is_pt_reception',
        store=True
    )

    is_satelite_reception = fields.Boolean(
        'Recepción Sételite',
        compute='_compute_is_satelite_reception',
        store=True
    )

    # carrier_id = fields.Many2one('custom.carrier', 'Conductor')

    truck_in_date = fields.Datetime(
        'Entrada de Camión',
        readonly=True
    )

    elapsed_time = fields.Char(
        'Horas Camión en planta',
        compute='_compute_elapsed_time'
    )

    avg_unitary_weight = fields.Float(
        'Promedio Peso unitario',
        compute='_compute_avg_unitary_weight',
        digits=dp.get_precision('Product Unit of Measure')
    )

    quality_weight = fields.Float(
        'Kilos Calidad',
        track_visibility='onchange',
        digits=dp.get_precision('Product Unit of Measure')
    )

    carrier_rut = fields.Char(
        'Rut',
        # related='carrier_id.rut'
    )

    carrier_cell_phone = fields.Char(
        'Celular',
        # related='carrier_id.cell_number'
    )

    carrier_truck_patent = fields.Char(
        'Patente Camión (Texto)',
        # related='truck_id.name'
    )

    carrier_cart_patent = fields.Char(
        'Patente Carro (Texto)',
        # related='cart_id.name'
    )

    truck_id = fields.Many2one(
        'transport',
        'Patente Camión',
        context={'default_is_truck': True},
        domain=[('is_truck', '=', True)]
    )

    cart_id = fields.Many2one(
        'transport',
        'Patente Carro',
        context={'default_is_truck': False},
        domain=[('is_truck', '=', False)]

    )

    hr_alert_notification_count = fields.Integer('Conteo de notificación de retraso de camión')

    kg_diff_alert_notification_count = fields.Integer('Conteo de notificación de diferencia de kg')

    sag_code = fields.Char(
        'CSG',
        compute='compute_sag_code'
    )

    is_pt_dispatch = fields.Boolean('Es PT Despacho', compute='_compute_is_pt_dispatch')

    reception_alert = fields.Many2one('reception.alert.config')

    harvest = fields.Char(
        'Cosecha',
        default=datetime.now().year
    )

    is_returned = fields.Boolean('Fue Devuelvo?')

    is_return = fields.Boolean('Es Devolucion?')

    picking_return_id = fields.Many2one('stock.picking', string='Devuelto de ')

    display_net_weight = fields.Float('Kilos Netos a mostrar', compute='compute_display_net_weight')



    @api.depends('partner_id')
    def compute_sag_code(self):
        for item in self:
            item.sag_code = item.partner_id.sag_code
            return

    @api.multi
    def compute_display_net_weight(self):
        for item in self:
            if item.picking_type_code == 'incoming':
                item.display_net_weight = item.net_weight
            elif item.picking_type_code == 'outgoing':
                item.display_net_weight = item.net_weight_dispatch
            else:
                item.display_net_weight = 0

    @api.multi
    def gross_weight_button(self):
        data = self._get_data_from_weigh()
        self.write({
            'gross_weight': float(data)
        })

    @api.multi
    def button_weight_tare(self):
        data = self._get_data_from_weigh()
        if not self.gross_weight:
            raise models.ValidationError('Debe ingresar el peso bruto')
        self.write({
            'tare_weight': float(data)
        })

    @api.one
    @api.depends('tare_weight', 'gross_weight', 'move_ids_without_package', 'quality_weight', 'is_return')
    def _compute_net_weight(self):
        if self.picking_type_code == 'incoming':
            self.net_weight = self.gross_weight - self.tare_weight + self.quality_weight
            if self.is_mp_reception or self.is_pt_reception or self.is_satelite_reception:
                if self.canning_weight:
                    self.net_weight = self.net_weight - self.canning_weight
        elif self.picking_type_code == 'incoming' and self.is_return:
            if len(self.move_ids_without_package) > 0:
                self.net_weight = self.move_ids_without_package[0].product_uom_qty

    @api.one
    @api.depends('move_ids_without_package')
    def _compute_weight_guide(self):
        if self.picking_type_code == 'incoming':
            m_move = self.get_mp_move()
            if not m_move:
                m_move = self.get_pt_move()
            if not m_move:
                m_move = self.get_product_move()
            if m_move:
                self.weight_guide = m_move[0].product_uom_qty

    @api.one
    @api.depends('move_ids_without_package')
    def _compute_canning_weight(self):
        if self.picking_type_code == 'incoming':
            canning = self.get_canning_move()
            if len(canning) == 1 and canning.product_id.weight:
                self.canning_weight = canning.product_uom_qty * canning.product_id.weight

    @api.model
    @api.onchange('gross_weight')
    def on_change_gross_weight(self):
        if self.picking_type_code == 'incoming':
            message = ''
            if self.gross_weight < self.weight_guide:
                message += 'Los kilos brutos deben ser mayor a los kilos de la guía'
                self.gross_weight = 0
            if message:
                raise models.ValidationError(message)

    @api.one
    @api.depends('tare_weight', 'gross_weight', 'move_ids_without_package')
    def _compute_production_net_weight(self):
        if self.picking_type_code == 'incoming':
            self.production_net_weight = self.gross_weight - self.tare_weight + self.quality_weight
            if self.is_mp_reception or self.is_pt_reception or self.is_satelite_reception:
                if self.canning_weight:
                    self.production_net_weight = self.production_net_weight - self.canning_weight

    @api.one
    def _compute_elapsed_time(self):
        if self.truck_in_date:
            if self.date_done:
                self.elapsed_time = self._get_hours(self.truck_in_date, self.date_done)
            else:

                self.elapsed_time = self._get_hours(self.truck_in_date, datetime.now())
        else:
            self.elapsed_time = '00:00:00'

    @api.one
    @api.depends('picking_type_id')  # 'reception_type_selection',
    def _compute_is_mp_reception(self):
        # self.reception_type_selection == 'mp' or \
        self.is_mp_reception = self.picking_type_id.warehouse_id.name and \
                               'materia prima' in str.lower(self.picking_type_id.warehouse_id.name) and \
                               self.picking_type_id.name and 'recepciones' in str.lower(self.picking_type_id.name)

    @api.one
    @api.depends('picking_type_id')
    def _compute_is_pt_reception(self):
        if self.picking_type_code == 'incoming':
            self.is_pt_reception = 'producto terminado' in str.lower(self.picking_type_id.warehouse_id.name) and \
                                   'recepciones' in str.lower(self.picking_type_id.name)

    @api.one
    @api.depends('picking_type_id')
    def _compute_is_pt_dispatch(self):
        self.is_pt_reception = 'producto terminado' in str.lower(self.picking_type_id.warehouse_id.name) and \
                               'ordenes de entrega' in str.lower(self.picking_type_id.name)

    @api.one
    @api.depends('picking_type_id')
    def _compute_is_satelite_reception(self):
        if self.picking_type_code == 'incoming':
            self.is_satelite_reception = 'packing' in str.lower(self.picking_type_id.warehouse_id.name) and \
                                         'recepciones' in str.lower(self.picking_type_id.name)

    @api.one
    @api.depends('net_weight', 'tare_weight', 'gross_weight', 'move_ids_without_package')
    def _compute_avg_unitary_weight(self):
        if self.picking_type_code == 'incoming':
            if self.net_weight:
                canning = self.get_canning_move()
                if len(canning) == 1:
                    divisor = canning.product_uom_qty
                    if divisor == 0:
                        divisor = 1

                    self.avg_unitary_weight = self.net_weight / divisor

    @api.model
    def get_mp_move(self):
        return self.move_ids_without_package.filtered(lambda x: x.product_id.categ_id.is_mp is True)

    @api.model
    def get_pt_move(self):
        return self.move_ids_without_package.filtered(lambda a: a.product_id.categ_id.is_pt)

    @api.model
    def get_canning_move(self):
        return self.move_ids_without_package.filtered(lambda x: x.product_id.categ_id.is_canning is True)

    def _get_hours(self, init_date, finish_date):
        diff = str((finish_date - init_date))
        return diff.split('.')[0]

    def _get_data_from_weigh(self):
        try:
            weighbridge_communication_address = self.env['ir.config_parameter'].sudo().get_param(
                'dimabe_reception.weighbridge_communication_address')
            if weighbridge_communication_address and weighbridge_communication_address != '':
                res = requests.request('POST', weighbridge_communication_address)
                json_data = json.loads(res.text.strip())
                return json_data['value']
            else:
                raise models.ValidationError('La direccion de equipo de romana no se encuentra definida, por favor comunicarse con el administrador')
        except Exception as e:
            if 'HTTPConnectionPool' in str(e):
                raise models.ValidationError(
                    "Por favor comprobar si el equipo de romana se encuentre encendido o con conexion a internet")
            else:
                raise models.ValidationError(str(e))

    def get_product_move(self):
        return self.move_ids_without_package.filtered(
            lambda x: x.product_id.categ_id.id in self.picking_type_id.warehouse_id.products_can_be_stored.filtered(
                lambda y: not y.reserve_ignore).ids)[0] if self.move_ids_without_package.filtered(
            lambda x: x.product_id.categ_id.id in self.picking_type_id.warehouse_id.products_can_be_stored.filtered(
                lambda y: not y.reserve_ignore).ids) else None

    @api.multi
    def action_confirm(self):
        if self.picking_type_code == 'incoming' and self.picking_type_id.show_in_canning_report:
            if self.guide_number == 0:
                raise models.ValidationError('Debe ingresar numero de guía')
        if self.picking_type_code == 'incoming' and not self.is_return:
            for stock_picking in self:
                if stock_picking.is_mp_reception or stock_picking.is_pt_reception:
                    stock_picking.validate_mp_reception()
                    stock_picking.truck_in_date = fields.datetime.now()
                res = super(StockPicking, self).action_confirm()
                _logger.info('LOG: -->> res etapa 1 %s' % res)
                m_move = stock_picking.get_mp_move()
                if not m_move:
                    m_move = stock_picking.get_pt_move()
                if not m_move:
                    m_move = stock_picking.get_product_move()
                _logger.info('LOG: -->> res etapa 2 %s' % res)
                if m_move:
                    
                    if not m_move.move_line_ids or len(m_move.move_line_ids) == 0:
                        for move in stock_picking.move_ids_without_package:
                            self.env['stock.move.line'].create({
                                'move_id': move.id,
                                'picking_id': stock_picking.id,
                                'product_id': move.product_id.id,
                                'product_uom_id': move.product_id.uom_id.id,
                                'product_uom_qty': move.product_uom_qty,
                                'location_id': 9,
                                'location_dest_id': stock_picking.location_dest_id.id,
                                'date': date.today(),
                            })
                    _logger.info('LOG: -->> res etapa 3 pasa  %s' % res)
                if m_move and m_move.move_line_ids and m_move.picking_id.picking_type_code == 'incoming':
                    for move_line in m_move.move_line_ids:
                        lot = self.env['stock.production.lot'].create({
                            'name': stock_picking.name,
                            'product_id': move_line.product_id.id,
                            'standard_weight': stock_picking.net_weight,
                            'producer_id': stock_picking.partner_id.id,
                            'origin_process': 'RECEPCIÓN'
                        })
                        if lot:
                            move_line.update({
                                'lot_id': lot.id
                            })
                    _logger.info('LOG: -->> res etapa 4 pasa  %s' % res)

                    if m_move.product_id.tracking == 'lot' and not m_move.has_serial_generated:
                        _logger.info('LOG: -->> res etapa 5 pasa  %s' % res)

                        for idx, stock_move_line in enumerate(m_move.move_line_ids):
                            

                            if m_move.product_id.categ_id.is_mp or m_move.product_id.categ_id.is_pt or m_move == self.get_product_move():
                                
                                total_qty = m_move.picking_id.get_canning_move().product_uom_qty
                                # calculated_weight = stock_move_line.qty_done / total_qty

                                if stock_move_line.lot_id:
                                    _logger.info('LOG: -->> generando proceso %s de %s' % (idx + 1, len(m_move.move_line_ids)))
                                    default_value = stock_picking.avg_unitary_weight or 1
                                    for idy, i in enumerate(range(int(total_qty))):
                                        _logger.info('LOG: -->> iterando sobre cantidad %s de %s' % (idy + 1, int(total_qty)))
                                        if i == int(total_qty):

                                            diff = stock_picking.net_weight - (
                                                    int(total_qty) * default_value)

                                            tmp = '00{}'.format(i + 1)
                                            self.env['stock.production.lot.serial'].create({
                                                'calculated_weight': default_value + diff,
                                                'product_id': stock_move_line.product_id.id,
                                                'stock_production_lot_id': stock_move_line.lot_id.id,
                                                'serial_number': '{}{}'.format(stock_move_line.lot_name, tmp[-3:])
                                            })
                                        else:
                                            tmp = '00{}'.format(i + 1)
                                            self.env['stock.production.lot.serial'].create({
                                                'calculated_weight': default_value,
                                                'product_id': stock_move_line.product_id.id,
                                                'stock_production_lot_id': stock_move_line.lot_id.id,
                                                'serial_number': '{}{}'.format(stock_move_line.lot_name, tmp[-3:])
                                            })
                                    _logger.info('LOG: -->>> ***  sumatoria  ***')
                                    _logger.info('LOG: -->> escribiendo en stock_move_line  %s' % len(stock_move_line.lot_id.stock_production_lot_serial_ids))
                                    stock_move_line.lot_id.write({
                                        'available_kg': sum(
                                            stock_move_line.lot_id.stock_production_lot_serial_ids.mapped(
                                                'display_weight'))
                                    })
                                    m_move.has_serial_generated = True
                                    
                                    
                _logger.info('LOG: -->> res etapa 6 pasa  %s' % res)
                return res
        else:
            return super(StockPicking, self).action_confirm()

    @api.multi
    def button_validate(self):
        if self.picking_type_code == 'incoming' and not self.is_return:
            for stock_picking in self:
                message = ''
                if stock_picking.is_mp_reception or stock_picking.is_pt_reception:
                    if not stock_picking.gross_weight:
                        message = 'Debe agregar kg brutos \n'
                    if stock_picking.gross_weight < stock_picking.weight_guide:
                        message += 'Los kilos de la Guía no pueden ser mayores a los Kilos brutos ingresados \n'
                    if not stock_picking.tare_weight:
                        message += 'Debe agregar kg tara \n'
                    if not stock_picking.quality_weight and \
                            'verde' not in str.lower(stock_picking.picking_type_id.warehouse_id.name):
                        message += 'Los kilos de calidad aún no han sido registrados en el sistema,' \
                                   ' no es posible cerrar el ciclo de recepción'
                    if message:
                        raise models.ValidationError(message)
            res = super(StockPicking, self).button_validate()
            self.sendKgNotify()

            if self.get_mp_move() or self.get_pt_move():
                m_move = self.get_mp_move()
                if not m_move:
                    m_move = self.get_pt_move()
                m_move.quantity_done = self.net_weight
                m_move.product_uom_qty = self.weight_guide
                if m_move.has_serial_generated and self.avg_unitary_weight:
                    self.env['stock.production.lot.serial'].search([('stock_production_lot_id', '=', self.name)]).write(
                        {
                            'real_weight': self.avg_unitary_weight
                        })
                    canning = self.get_canning_move()
                    if len(canning) == 1:
                        diff = self.net_weight - (canning.product_uom_qty * self.avg_unitary_weight)
                        self.env['stock.production.lot.serial'].search([('stock_production_lot_id', '=', self.name)])[
                            -1].write({
                            'real_weight': self.avg_unitary_weight + diff
                        })
            if self.get_mp_move or self.get_pt_move() and self.get_product_move():
                m_move = self.get_mp_move()
                if self.get_mp_move():
                    lot = self.env['stock.move.line'].search([('move_id.id', '=', m_move.id)], limit=1)
                    lot.lot_id.write({
                        'available_kg': lot.qty_done
                    })
                    if not self.picking_type_id.require_dried:
                        self.env['report.raw.lot'].sudo().create({
                            'lot_id': lot.lot_id.id,
                            'producer_id': lot.lot_id.producer_id.id,
                            'product_id': lot.lot_id.product_id.id,
                            'available_weight': lot.qty_done,
                            'product_variety': lot.lot_id.product_id.get_variety(),
                            'product_caliber': lot.lot_id.product_id.get_calibers(),
                            'location_id': lot.location_dest_id.id,
                            'guide_number': lot.picking_id.guide_number,
                            'lot_harvest': self.harvest,
                            'date': datetime.now(),
                            'reception_weight': lot.lot_id.reception_weight,
                            'available_series': len(lot.lot_id.stock_production_lot_serial_ids),
                        })
                if not m_move:
                    m_move = self.get_pt_move()
                if not m_move:
                    m_move = self.get_product_move()
                if m_move and self.picking_type_id.require_dried:
                    lot = self.env['stock.move.line'].search([('move_id.id', '=', m_move.id)], limit=1)
                    lot.lot_id.write({
                        'available_kg': lot.qty_done
                    })
            return res
        # Se usaran datos de modulo de dimabe_manufacturing
        elif self.picking_type_code == 'incoming' and self.is_return:
            for line in self.move_line_ids_without_package:
                if line.lot_id:
                    test = self.picking_return_id.packing_list_ids.filtered(
                        lambda x: x.stock_production_lot_id.id == line.lot_id.id)
                    self.picking_return_id.packing_list_ids.filtered(
                        lambda x: x.stock_production_lot_id.id == line.lot_id.id).write({
                        'consumed': False,
                        'reserved_to_stock_picking_id': None
                    })
                    self.picking_return_id.assigned_pallet_ids.write({
                        'reserved_to_stock_picking_id': None
                    })
        elif self.picking_type_code == 'outgoing':
            if self.is_multiple_dispatch:
                view = self.env.ref('dimabe_manufacturing.view_principal_order')
                wiz = self.env['confirm.principal.order'].create({
                    'sale_ids': [(4, s.id) for s in self.dispatch_line_ids.mapped('sale_id')],
                    'picking_id': self.id,
                    'custom_dispatch_line_ids': [(4, c.id) for c in self.dispatch_line_ids]
                })
                return {
                    'name': 'Desea que todos los documentos se carguen con el # de pedido principal?',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'confirm.principal.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context
                }
            self.packing_list_ids.sudo().write({
                'consumed': True
            })

        res = super(StockPicking, self).button_validate()
        return res

    def clean_reserved(self):
        for lot in self.move_line_ids_without_package.mapped('lot_id'):
            if lot not in self.packing_list_lot_ids:
                query = f"DELETE FROM stock_move_line where lot_id = {lot.id} and picking_id = {self.id}"
                cr = self._cr
                cr.execute(query)

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        if self.picking_type_code == 'outgoing':
            for lot in self.move_line_ids_without_package.mapped('lot_id'):
                lot.update_stock_quant(self.location_id.id)

        return res

    @api.multi
    def action_done(self):
        super(StockPicking, self).action_done()
        if self.picking_type_code == 'outgoing':
            for lot in self.move_line_ids_without_package.mapped('lot_id'):
                lot.update_stock_quant(self.location_id.id)

    @api.model
    def validate_mp_reception(self):
        return True

    @api.multi
    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return base_url

    def sendKgNotify(self):
        if self.kg_diff_alert_notification_count == 0:
            if self.weight_guide > 0 and self.net_weight > 0:
                alert_config = self.env['reception.alert.config'].search([])
                if abs(self.weight_guide - self.net_weight) > alert_config.kg_diff_alert:
                    self.ensure_one()
                    self.reception_alert = alert_config
                    template_id = self.env.ref('dimabe_reception.diff_weight_alert_mail_template')
                    self.message_post_with_template(template_id.id)
                    self.kg_diff_alert_notification_count += self.kg_diff_alert_notification_count

    @api.multi
    def notify_alerts(self):
        alert_config = self.env['reception.alert.config'].search([])
        elapsed_datetime = datetime.strptime(self.elapsed_time, '%H:%M:%S')
        if self.hr_alert_notification_count == 0 and elapsed_datetime.hour >= alert_config.hr_alert:
            self.ensure_one()
            self.reception_alert = alert_config
            template_id = self.env.ref('dimabe_reception.truck_not_out_mail_template')
            self.message_post_with_template(template_id.id)
            self.hr_alert_notification_count += 1

    @api.model
    def create(self, values_list):
        res = super(StockPicking, self).create(values_list)

        res.validate_same_product_lines()

        return res

    @api.multi
    def write(self, vals):
        res = super(StockPicking, self).write(vals)

        for item in self:
            item.validate_same_product_lines()
        self.id

        return res

    @api.model
    def validate_same_product_lines(self):
        if self.is_mp_reception:
            if len(self.move_ids_without_package) > len(self.move_ids_without_package.mapped('product_id')):
                raise models.ValidationError('no puede tener el mismo producto en más de una linea')

    def update_stock_quant(self, lot_name, location_id):
        lot = self.env['stock.production.lot'].search([('name', '=', self.name)])
        if lot.stock_production_lot_serial_ids.filtered(lambda a: not a.consumed):

            quant = self.env['stock.quant'].sudo().search(
                [('lot_id', '=', lot.id), ('location_id.usage', '=', 'internal'), ('location_id', '=', location_id)])

            if quant:
                quant.write({
                    'reserved_quantity': sum(lot.stock_production_lot_serial_ids.filtered(lambda
                                                                                              x: x.reserved_to_stock_picking_id and x.reserved_to_stock_picking_id.state != 'done' and not x.consumed).mapped(
                        'display_weight')),
                    'quantity': sum(lot.stock_production_lot_serial_ids.filtered(
                        lambda x: not x.reserved_to_stock_picking_id and not x.consumed).mapped('display_weight'))
                })
            else:
                self.env['stock.quant'].sudo().create({
                    'lot_id': lot.id,
                    'product_id': lot.product_id.id,
                    'reserved_quantity': sum(lot.stock_production_lot_serial_ids.filtered(lambda
                                                                                              x: x.reserved_to_stock_picking_id and x.reserved_to_stock_picking_id.state != 'done' and not x.consumed).mapped(
                        'display_weight')),
                    'quantity': sum(lot.stock_production_lot_serial_ids.filtered(
                        lambda x: not x.reserved_to_stock_picking_id and not x.consumed).mapped('display_weight')),
                    'location_id': location_id
                })

    def action_modify(self):
        for item in self:
            self.validate_lot()
            if any(line.lot_id for line in item.move_line_ids_without_package):
                item.move_line_ids_without_package.filtered(
                    lambda x: x.lot_id).lot_id.sudo().stock_production_lot_serial_ids.sudo()
                item.move_line_ids_without_package.filtered(
                    lambda x: x.lot_id).lot_id.quant_ids.sudo().unlink()
                item.move_line_ids_without_package.filtered(
                    lambda x: x.lot_id).lot_id.sudo().unlink()
            item.write({
                'state': 'draft',
            })
            item.move_ids_without_package.sudo().write({
                'state': 'draft',
                'has_serial_generated': False
            })
            item.move_line_ids_without_package.sudo().write({
                'state': 'draft'
            })
            item.move_line_ids_without_package.sudo().unlink()
            item.message_post(f'Se procede a volver a habilitar la modificación de recepcion {item.name}',
                              'Modificacion de recepción')

    def action_delete(self):
        for item in self:
            self.validate_lot()
            view_id = self.env.ref('dimabe_reception.delete_picking_lot_form_wizard_view')
            lot_id = item.move_line_ids_without_package.mapped('lot_id')
            wiz_id = self.env['delete.picking.lot'].sudo().create({
                'picking_name': item.name,
                'lot_name': lot_id.name,
                'picking_id': item.id,
                'picking_type_id': item.picking_type_id.id,
                'user_id': self.env.uid,
                'is_done': True,
            })

            return {
                'name': f'Eliminar recepción {item.name}',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'delete.picking.lot',
                'target': 'new',
                'res_id': wiz_id.id,
                'context': self.env.context,
                'views': [(view_id.id, 'form')]
            }

    def validate_lot(self):
        for item in self:
            lot_id = self.move_line_ids_without_package.mapped('lot_id')
            if any(serial.consumed for serial in lot_id.stock_production_lot_serial_ids):
                raise models.ValidationError(
                    'No se puede realizar la acción, ya que el lote ya fue utilizado en un proceso de producción')
