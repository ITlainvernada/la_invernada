from odoo import fields,models,api

class CustomDispatchLine(models.Model):
    _name = 'custom.dispatch.line'

    sale_id = fields.Many2one('sale.order','Pedido')

    dispatch_id = fields.Many2one('stock.picking','Despacho')

    product_id = fields.Many2one('product.product','Producto')

    required_sale_qty = fields.Float('Cantidad Requerida')

    real_dispatch_qty = fields.Float('Cantidad Real')


