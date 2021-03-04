from odoo import fields,models,api

class CustomDispatchLine(models.Model):
    _name = 'custom.dispatch.line'

    sale_id = fields.Many2one('sale.order','Pedido')

    dispatch_real_id = fields.Many2one('stock.picking','Despacho Odoo')

    dispatch_id = fields.Many2one('stock.picking','Despacho')

    product_id = fields.Many2one('product.product','Producto')

    required_sale_qty = fields.Float('Cantidad Requerida')

    real_dispatch_qty = fields.Float('Cantidad Real')

    is_select = fields.Boolean('Pedido Principal')

    move_line_ids = fields.Many2many('stock.move.line',string='Movimientos')



