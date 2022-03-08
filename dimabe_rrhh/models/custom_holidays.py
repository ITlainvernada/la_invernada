from odoo import models, fields, api
from odoo.models import UserError


class CustomHolidays(models.Model):
    _name = 'custom.holidays'
    _description = "Ausencia Legal"

    name = fields.Char('Nombre')

    date = fields.Date('Fecha')

    type = fields.Selection([('Civil', 'Civil'), ('Religioso', 'Religioso')])

    inalienable = fields.Boolean('Irrenunciable')