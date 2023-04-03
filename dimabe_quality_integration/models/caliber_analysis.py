from odoo import fields, models, api


class CaliberAnalysis(models.Model):
    _name = 'caliber.analysis'

    ref = fields.Integer('Referencia')

    name = fields.Char('Calibre')

    percent = fields.Float('Porcentaje')

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')
