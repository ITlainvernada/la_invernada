from odoo import fields, models, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    lot_quality_analysis_id = fields.Many2one(
        related='lot_id.quality_analysis_id',
        string='Análisis de Calidad'
    )
