from odoo import models, fields, api


class InternalDamageAnalysis(models.Model):
    _name = 'internal.damage.analysis'

    ref = fields.Integer('Referencia')

    name = fields.Char('Daño Interno')

    percent = fields.Float('Porcentaje')

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')
