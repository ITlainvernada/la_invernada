from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sag_code = fields.Char('CSG', tracking='always')

    is_sag_active = fields.Boolean(
        'SAG Activo',
        default=False,
        tracking='always',
    )

    name = fields.Char(tracking='always')

    short_name = fields.Char(
        'Nombre Corto',
        compute='_compute_short_name'
    )

    @api.one
    def _compute_short_name(self):
        if self.name:
            self.short_name = self.name[0:25]

    @api.model
    def create(self, values_list):
        res = super(ResPartner, self).create(values_list)
        return res
