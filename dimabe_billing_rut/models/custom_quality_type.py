from odoo import models, fields, api

class CustomQualityType(models.Model):

    _name = 'custom.quality.type'
    _description = "Tipo de Calidad"

    name = fields.Char(string= 'Nombre', required=True)