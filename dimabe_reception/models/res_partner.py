from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sag_code = fields.Char('CSG')

    is_sag_active = fields.Boolean(
        'SAG Activo',
        default=False
    )

    short_name = fields.Char(
        'Nombre Corto',
        compute='_compute_short_name'
    )

    type = fields.Selection(
        selection_add=[('ranch', 'Fundo')]
    )

    ranch_ids = fields.One2many('res.partner', 'parent_id', string='Fundos', domain=[('type', '=', 'ranch')])

    @api.one
    def _compute_short_name(self):
        if self.name:
            self.short_name = self.name[0:25]

    @api.model
    def create(self, values_list):
        res = super(ResPartner, self).create(values_list)
        return res

