from odoo import models, fields, api

class CustomFreightPaymentTerm(models.Model):

    _name = 'custom.freight.payment.term'
    _description = "Plazo de Pago Flete"

    name = fields.Char(string= 'Nombre', required=True)
