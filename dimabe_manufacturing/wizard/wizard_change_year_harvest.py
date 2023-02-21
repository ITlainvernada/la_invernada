from odoo import fields, models, api


class WizardChangeYearHarvest(models.TransientModel):
    _name = 'wizard.change.year.harvest'

    year = fields.Integer('Año de cosecha')
    lot_id = fields.Many2one('stock.production.lot', string='Lote')
    message = fields.Html('Mensaje', compute='compute_message')

    def change_harvest(self):
        for item in self:
            item.lot_id.write({
                'harvest': item.year,
            })

    def compute_message(self):
        for item in self:
            message = f'<h4>¿Esta seguro de cambiar el año de cosecha del lote {item.lot_id.name} a año {item.year}?</h4>'
            item.message = message
