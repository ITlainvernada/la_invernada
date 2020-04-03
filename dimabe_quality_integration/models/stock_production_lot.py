from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')

    balance = fields.Float(
        'Stock Disponible',
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_balance',
        search='_search_balance'
    )

    @api.multi
    def _compute_balance(self):
        for item in self:
            item.balance = item.get_stock_quant().balance

    def _search_balance(self, operator, value):
        lot_ids = self.env['stock.quant'].search([
            ('balance', operator, value),
            ('location_id.name', '=', 'Stock')
        ]).mapped('lot_id')
        models._logger.error(lot_ids.mapped('name'))
        return [('id', 'in', lot_ids.mapped('id'))]
