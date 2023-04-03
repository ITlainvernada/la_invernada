from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    always_to_print = fields.Boolean('Mostrar Siempre en Impresión se Etiquetas')

    region_address_id = fields.Many2one(
        'region.address',
        'Región',
        track_visibility='always'
    )

    city_address = fields.Char(
        'Comuna',
        compute='_compute_city_address',
    track_visibility = 'always'
    )

    state_id_address = fields.Many2one(
        'res.country.state',
        'Provincia',
        track_visibility='always',
        compute='_compute_state_id_address'
    )

    region_address_id_address = fields.Many2one(
        'region.address',
        'Región',
        track_visibility='always',
        compute='_compute_region_address_id_address'
    )

    is_warehouse_notify = fields.Boolean(
        'Notificar Movimiento de Materia',
        track_visibility='always'
    )

    @api.multi
    def _compute_city_address(self):
        for item in self:
            address_child = item.get_address_child()
            if address_child:
                item.city_address = address_child[0].city

    @api.multi
    def _compute_state_id_address(self):
        for item in self:
            address_child = item.get_address_child()
            if address_child:
                item.state_id_address = address_child[0].state_id

    @api.multi
    def _compute_region_address_id_address(self):
        for item in self:
            address_child = item.get_address_child()
            if address_child:
                item.region_address_id_address = address_child[0].region_address_id

    @api.model
    def get_address_child(self):
        return self.child_ids.filtered(
                lambda a: a.type == 'delivery'
            )


