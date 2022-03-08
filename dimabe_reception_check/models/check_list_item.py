from odoo import models, fields


class CheckListItem(models.Model):

    _name = 'check.list.item'
    _description = "Item de Check List"

    name = fields.Char('Nombre', required=True)

    position = fields.Integer('Posición')

    _order = 'position'

