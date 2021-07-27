
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_purchase_price = fields.Float(
        string='Last Purchase Price', compute='_compute_last_purchase')
    last_purchase_date = fields.Date(
        string='Last Purchase Date', compute='_compute_last_purchase')
    last_supplier_id = fields.Many2one(
        comodel_name='res.partner', string='Last Supplier',
        compute='_compute_last_purchase')
    last_purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line', string='Last Purchase Line',
        compute='_compute_last_purchase')
    
    @api.multi
    def _compute_last_purchase(self):
        """ Get last purchase price, last purchase date and last supplier """
        PurchaseOrderLine = self.env['purchase.order.line']
        for product in self:
            lines = PurchaseOrderLine.search(
                [('product_id', '=', product.id),
                 ('state', 'in', ['purchase', 'done'])]).sorted(
                key=lambda l: l.order_id.date_order, reverse=True)
            if lines:
                product.last_purchase_date = fields.Datetime.context_timestamp(self, lines[:1].order_id.date_order).strftime(DF)
                product.last_purchase_price = lines[:1].price_unit
                product.last_supplier_id = lines[:1].order_id.partner_id
                product.last_purchase_line_id = lines[:1]