from odoo import models, fields, api
import re

class CustomAccountInvoiceLine(models.Model):
    _name = "custom.account.invoice.line"

    invoice_id = fields.Many2one('account.invoice',string="Factura")

    product_id = fields.Many2one('product.product',string="Producto")

    account_id = fields.Many2one('account.account', string="Cuenta")

    quantity = fields.Float(string="Cantidad", compute="_compute_quantity")

    uom_id = fields.Many2one('uom.uom',string="Unidad de medida")

    price_unit = fields.Float(string="Precio")

    name = fields.Text(string="Descripción", required=True)

    price_subtotal = fields.Float(string="Subtotal", compute="_compute_price_subtotal")

    canning_quantity = fields.Float(string="Cantidad de Envases", compute="_compute_canning_quantiy")

    def _compute_quantity(self):
        for item in self:
            invoice_line = self.env['account.invoice.line'].search([('invoice_id','=',item.invoice_id.id),('product_id','=',item.product_id.id)])
            item.quantity = sum(line.quantity for line in invoice_line)

    def _compute_price_subtotal(self):
        for item in self:
            if item.price_unit and item.quantity:
                item.price_subtotal = item.price_unit * item.quantity

    def _compute_canning_quantiy(self):
        for item in self:
            for attr in item.product_id.attribute_value_ids:
                is_kg = attr.attribute_id.name.find('K')
                if attr.attribute_id.name == 'Tipo de envase' and is_kg != 1:
                    value = [float(char) for char in re.findall(r'-?\d+\.?\d*',attr.name)]
                    item.canning_quantity = item.quantity / value[0]
                





