from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    require_dried = fields.Boolean(
        'Requiere de Secado'
    )

    is_pt = fields.Boolean('Es Despacho Pt')

    show_in_canning_report = fields.Boolean('Mostrar en reporte de control de envases')
