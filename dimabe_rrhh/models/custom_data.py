from odoo import models, fields


class CustomData(models.Model):
    _name = 'custom.data'
    _description = "Datos"

    name = fields.Char('Nombre')

    value = fields.Float('Valor')

    comment = fields.Char('Comentario')
