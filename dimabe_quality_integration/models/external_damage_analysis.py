from odoo import fields, models, api


class ExternalDamageAnalysis(models.Model):
    _name = 'external.damage.analysis'

    ref = fields.Integer('Referencia')

    name = fields.Char('Daño  Externo')

    percent = fields.Float('Porcentaje')

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')
