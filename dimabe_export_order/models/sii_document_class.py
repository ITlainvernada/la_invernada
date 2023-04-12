from odoo import models, fields


class SiiDocumentClass(models.Model):
    _inherit = 'sii.document_class'

    last_caf_consumed = fields.Char('Ultimo folio consumido')

    def get_last_caf_consumed(self):
        for item in self:
            if item.sii_code == 52:
                records = self.env['stock.picking'].sudo().search(
                    [('use_documents', '=', True), ('location_id.sii_document_class_id.id', '=', item.id),
                     ('state', '=', 'done')]).filtered(lambda x: x.sii_result not in ['NoEnviado', '']).mapped(
                    'sii_document_number')
                current_document_number = max(int(record) for record in records) + 1
                return current_document_number

    def verify_sii_document_number(self, document_number):
        last_caf_charged = max(caf.final_nm for caf in
                               self.env['dte.caf'].sudo().search([('sii_document_class', '=', self.sii_code)]))
        if document_number > last_caf_charged:
            raise models.UserError(
                'No cuenta con folio disponible para la tipo de documento {}'.format(self.display_name))
