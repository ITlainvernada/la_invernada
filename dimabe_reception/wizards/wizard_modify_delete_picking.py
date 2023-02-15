from odoo import fields, models, api


class WizardModifyDeletePicking(models.TransientModel):
    _name = 'wizard.modify.delete.picking'

    picking_id = fields.Many2one('stock.picking', string='Recepción')
