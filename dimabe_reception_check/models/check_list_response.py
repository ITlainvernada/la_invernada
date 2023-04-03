from odoo import models, fields


class CheckListResponse(models.Model):

    _name = 'check.list.response'

    item = fields.Many2one(
        'check.list.item',
        'item',
        readonly=True
    )

    picking_id = fields.Many2one(
        'stock.picking',
        'Recepción',
        readonly=True
    )

    response = fields.Selection(
        [
            ('na', 'No aplica'),
            ('yes', 'Sí'),
            ('not', 'No')
        ],
        'Revisión'
    )

    documents = fields.Binary(
        'Adjuntos'
    )

    observation = fields.Text(
        'Observación',
        nullable=True,
        default=None
    )
