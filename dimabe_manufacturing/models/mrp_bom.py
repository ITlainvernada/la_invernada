from odoo import fields, models, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom.line'

    @api.constrains('product_id')
    def test(self):
        for item in self:
            bom_line_id = item.bom_id.bom_line_ids.filtered(
                lambda x: x != item and x.product_id.id == item.product_id.id)
            if bom_line_id:
                raise models.ValidationError(f'El producto {item.product_id.display_name} se encuentra duplicado')
