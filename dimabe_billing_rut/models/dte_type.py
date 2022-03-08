from odoo import models, fields

class DteType(models.Model):
    _name = 'dte.type'
    _description = "Tipo de DTE (Custom)"
    code = fields.Char('Código')
    name = fields.Char('Nombre')