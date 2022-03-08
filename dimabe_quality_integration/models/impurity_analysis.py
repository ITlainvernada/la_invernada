from odoo import fields, models, api


class ImpurityAnalysis(models.Model):
    _name = 'impurity.analysis'
    _description = "Analisis de Impureza"

    ref = fields.Integer('Referencia')

    name = fields.Char('Impureza')

    percent = fields.Float('Promedio')

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')
