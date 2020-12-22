from odoo import models, fields, api

class CustomInvoiceObservations(models.Model):
    _name = 'custom.invoice.observations'

    observations = fields.Char(
        string='Observación',
        nullable = True,
        default= None,
        size=140
    )