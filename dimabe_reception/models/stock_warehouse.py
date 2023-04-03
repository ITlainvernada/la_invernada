from odoo import models, fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    products_can_be_stored = fields.Many2many(
        'product.category',
        string='Productos que pueden ser almacenados'
    )

    csp = fields.Char('csp')
