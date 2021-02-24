from odoo import models, fields, api
import base64
from datetime import date


class ConfirmPrincipalOrde(models.TransientModel):
    _name = 'confirm.principal.order'

    sale_ids = fields.Many2many('sale.order')

    sale_id = fields.Many2one('sale.order')

    picking_id = fields.Many2one('stock.picking')

    custom_dispatch_line_ids = fields.Many2many('custom.dispatch.line')

    @api.one
    def select(self):
        self.process_data()
        self.custom_dispatch_line_ids.filtered(lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.write({
            'consignee_id': self.custom_dispatch_line_ids.filtered(
                lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.consignee_id.id,
            'notify_ids': [(4, n) for n in self.picking_id.notify_ids.mapped('id')]
        })
        report = self.env.ref('dimabe_export_order.action_packing_list').render_qweb_pdf(
            self.custom_dispatch_line_ids.filtered(lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.id)
        for item in self.custom_dispatch_line_ids:
            item.dispatch_id.write({
                'packing_list_file': base64.b64encode(report[0])
            })

    @api.one
    def cancel(self):
        self.process_data()
        self.custom_dispatch_line_ids.filtered(lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.write({
            'consignee_id': self.custom_dispatch_line_ids.filtered(
                lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.consignee_id.id,
            'notify_ids': [(4, n) for n in self.picking_id.notify_ids.mapped('id')]
        })
        report = self.env.ref('dimabe_export_order.action_packing_list').render_qweb_pdf(
            self.custom_dispatch_line_ids.filtered(lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.id)
        for item in self.picking_id.dispatch_line_ids:
            item.dispatch_id.write({
                'packing_list_file': base64.b64encode(report[0])
            })

    def process_data(self):
        for item in self.custom_dispatch_line_ids:
            if item.dispatch_id.id == self.picking_id.id:
                self.picking_id.button_validate()
                continue
            item.dispatch_id.clean_reserved(item.dispatch_id)
            for line in self.picking_id.move_line_ids_without_package.filtered(
                    lambda a: a.product_id.id == item.product_id.id):
                self.env['stock.move.line'].create({
                    'move_id': item.dispatch_id.move_ids_without_package.filtered(
                        lambda m: m.product_id.id == item.product_id.id).id,
                    'product_id': item.product_id.id,
                    'picking_id': item.dispatch_id.id,
                    'product_uom_id': item.product_id.uom_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'qty_done': line.product_uom_qty,
                    'state':'done',
                    'location_id': line.location_id.id,
                    'location_dest_id': item.dispatch_id.partner_id.property_stock_customer.id,
                    'date': line.date,
                    'lot_id': line.lot_id.id
                })
            if item.real_dispatch_qty > 0 and item.dispatch_id.id != self.picking_id.id:
                item.dispatch_id.write({
                    'state':'done'
                })
