from odoo import models, fields
class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    weighbridge_communication_address = fields.Char(
        "Direccion de comunicacion con Romana",
        config_parameter='dimabe_reception.weighbridge_communication_address'
    )