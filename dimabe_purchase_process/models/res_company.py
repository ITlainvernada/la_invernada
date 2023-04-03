from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    billing_mail = fields.Char(
        'Casilla de Correo para Facturación'
    )

    billing_email = fields.Char(
        'Correo Electrónico para Facturación'
    )
