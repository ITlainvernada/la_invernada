from odoo import models, fields, api

class CustomSafeType(models.Model):

    _name = 'custom.safe.type'
    _description = "Tipo de Seguro"

    name = fields.Char(string= 'Nombre', required=True)
