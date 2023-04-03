from odoo import fields, models, api


class HumidityAnalysis(models.Model):
    _name = 'humidity.analysis'

    ref = fields.Integer('Referencia')

    name = fields.Char('Humedad')

    percent = fields.Float('Porcentaje')

    tolerance = fields.Float('Tolerancia Máxima')

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')
