from odoo import fields, models, api


class PerformanceAnalysis(models.Model):
    _name = 'performance.analysis'

    ref = fields.Integer('Referencia')

    name = fields.Char('Rendimiento')

    percent = fields.Float('Porcentaje')

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')
