# -*- coding: utf-8 -*-

from openerp import models, fields


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    excel_format = fields.Char(string='Formato Excel', default='_ * #,##0.00_) ;_ * - #,##0.00_) ;_ * "-"??_) ;_ @_ ', required=True)
