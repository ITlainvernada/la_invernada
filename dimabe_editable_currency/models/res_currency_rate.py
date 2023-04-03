from odoo import models, fields


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    rate = fields.Float(
        digits=(12, 10),
        default=1.0,
        help='The rate of the currency to the currency of rate 1'
    )
