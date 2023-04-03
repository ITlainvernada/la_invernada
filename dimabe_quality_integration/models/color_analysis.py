from odoo import fields, models, api


class ColorAnalysis(models.Model):
    _name = 'color.analysis'

    ref = fields.Integer('Referencia')

    name = fields.Char('Color')

    percent = fields.Float('Porcentaje')

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')
