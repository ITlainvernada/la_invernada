from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class CustomTemporarySerial(models.Model):
    _name = 'custom.temporary.serial'

    name = fields.Char('N° Serie')

    product_id = fields.Many2one('product.product', 'Producto')

    lot_id = fields.Many2one('stock.production.lot', 'Lote')

    producer_id = fields.Many2one('res.partner', string='Productor')

    packaging_date = fields.Date('Fecha Produccion', default=fields.Date.today())

    best_before_date = fields.Date('Consumir antes de')

    harvest = fields.Integer('Año de Cosecha')

    canning_id = fields.Many2one('product.product', 'Envase')

    net_weight = fields.Float('Peso Neto', digits=dp.get_precision('Product Unit of Measure'))

    gross_weight = fields.Float('Peso Bruto', digits=dp.get_precision('Product Unit of Measure'))

    label_durability_id = fields.Many2one('label.durability', 'Durabilidad Etiqueta')

    production_id = fields.Many2one('mrp.production', string='Produccion')

    to_print = fields.Boolean('A Imprimir')

    printed = fields.Boolean('Impresa')

    @api.multi
    def do_print(self):
        return self.env.ref(
            'dimabe_manufacturing.action_print_temporary_serial'
        ).report_action(self)

    @api.multi
    def get_full_url(self):
        for item in self:
            return self.env["ir.config_parameter"].sudo().get_param("web.base.url")

    @api.model
    def create(self, values):
        res = super(CustomTemporarySerial, self).create(values)
        production_id = self.env['mrp.workorder'].search([('final_lot_id.id', '=', res.lot_id.id)]).production_id
        canning_id = self.get_possible_canning_id(production_id.id)[0]
        res['gross_weight'] = res.net_weight + canning_id.weight
        return res

    def get_possible_canning_id(self, production_id):
        production_id = self.env['mrp.production'].search([('id', '=', production_id)])
        return production_id.bom_id.bom_line_ids.filtered(
            lambda a: 'envases' in str.lower(a.product_id.categ_id.name) or
                      'embalaje' in str.lower(a.product_id.categ_id.name)
                      or (
                              a.product_id.categ_id.parent_id and (
                              'envases' in str.lower(a.product_id.categ_id.parent_id.name) or
                              'embalaje' in str.lower(a.product_id.categ_id.parent_id.name))
                      )
        ).mapped('product_id')

    def create_serial(self, pallet_id):
        for item in self:
            self.env['stock.production.lot.serial'].create({
                'serial_number': item.name,
                'product_id': item.product_id.id,
                'display_weight': item.net_weight,
                'belongs_to_prd_lot': True,
                'pallet_id': pallet_id,
                'producer_id': item.producer_id.id,
                'best_before_date_new': item.best_before_date,
                'packaging_date': item.packaging_date,
                'stock_production_lot_id': item.lot_id.id,
            })
            item.unlink()
