from odoo import fields, models, api


class FormAnalysis(models.Model):
    _name = 'form.analysis'

    ref = fields.Integer('Referencia')

    name = fields.Char('Forma')

    percent = fields.Float('Promedio')

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')
