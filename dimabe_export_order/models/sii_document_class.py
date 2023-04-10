from odoo import models, fields


class SiiDocumentClass(models.Model):
    _inherit = 'sii.document_class'

    last_caf_consumed = fields.M
