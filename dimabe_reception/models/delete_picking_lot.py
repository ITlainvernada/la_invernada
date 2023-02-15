from odoo import models, fields, api


class DeletePickingLot(models.Model):
    _name = 'delete.picking.lot'

    picking_name = fields.Char('Operación')

    lot_name = fields.Char('Lote')


