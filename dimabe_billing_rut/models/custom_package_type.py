from odoo import models, fields

class CustomPackageType(models.Model):
    _name = 'custom.package.type'
    _description = "Tipo de Paquete (Custom)"

    code = fields.Char(string= 'Código', required=True)

    name = fields.Char(string= 'Nombre', required=True)

    short_name = fields.Char(string= 'Nombre Corto', required=True)


   