from odoo import models, fields, api


class SiiDocumentClass(models.Model):
    _inherit = 'sii.document_class'

    last_caf_consumed = fields.Char('Ultimo folio consumido')

    def get_last_caf_consumed(self):
        for item in self:
            items = []
            print(type(item.sii_code))
            if item.sii_code == 52:
                records = self.env['stock.picking'].sudo().search(
                    [('use_documents', '=', True), ('location_id.sii_document_class_id.id', '=', item.id),
                     ('state', '=', 'done')]).filtered(lambda x: x.sii_result not in ['NoEnviado', '']).mapped(
                    'sii_document_number')
            return max(int(record) for record in records)
