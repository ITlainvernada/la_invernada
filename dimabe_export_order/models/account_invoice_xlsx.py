from odoo import fields, models, api

class AccountInvoiceXlsx(models.Model):
    _inherit = 'account.invoice.xlsx_mblz'

    @api.multi
    def generate_honorarios_book(self):
        file_name = 'honorarios.xlsx'
        workbook = xlsxwriter.Workbook(file_name, {'in_memory': True, 'strings_to_numbers': True})
        formats = self.set_formats(workbook)
        count_invoice = 0
        srow = 0
        for item in self:
            array_worksheet = []
            companies = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            company_name = ''
            begin = 0
            end = 0
            
            for com in companies:
                worksheet = workbook.add_worksheet(com.display_name)
                array_worksheet.append({
                    'company_object': com, 'worksheet': worksheet
                })
            for wk in array_worksheet:
                sheet = wk['worksheet']
                region = self.env['region.address'].search([('id', '=', 1)])
                titles = ['Cod.SII', 'Folio', 'Fecha', 'RUT', 'Nombre', '#', 'NETO', 'IMPTO (11.5%)']
                invoices_get_tax = self.env['account.invoice'].sudo().search(
                    [('document_class_id', '!=', None), ('company_id', '=', self.company_get_id.id),
                     ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
                taxes_title = list(
                    dict.fromkeys(invoices_get_tax.mapped('tax_line_ids').mapped('tax_id').mapped('name')))

                titles.append('Total')
                sheet.merge_range(0, 0, 0, 2, self.company_get_id.display_name, formats['title'])
                sheet.merge_range(1, 0, 1, 2, self.company_get_id.document_number, formats['title'])
                sheet.merge_range(2, 0, 2, 2,
                                  f'{self.company_get_id.city},Region {self.company_get_id.region_address_id.name}',
                                  formats['title'])
                sheet.merge_range(4, 3, 4, 6, 'Libro de Honorarios', formats['title'])
                sheet.merge_range(5, 3, 5, 6, 'Libro de Honorarios Ordenado por fecha', formats['title'])
                sheet.write(6, 8, 'Fecha', formats['title'])
                sheet.write(6, 9, date.today().strftime('%Y-%m-%d'), formats['title'])
                sheet.merge_range(6, 3, 6, 6, f'Desde {self.from_date} Hasta {self.to_date}', formats['title'])
                sheet.merge_range(7, 3, 7, 6, 'Moneda : Peso Chileno', formats['title'])
                row = 10
                col = 0
                
                for title in titles:
                    sheet.write(row, col, title, formats['title'])
                    col += 1
                row += 2
                col = 0
                sheet.merge_range(row, col, row, 5, 'Boleta de Honorarios Electrónica. (BHO)',
                                  formats['title'])
                row += 1
                domain_invoices = [('date', '>=', self.from_date),
                     ('type', 'in', ('in_invoice', 'in_refund')),
                     ('date', '<=', self.to_date), # TODO (71)
                     ('journal_id.employee_fee', '=', True),
                     ('company_id.id', '=', self.company_get_id.id)]
                #cambio en Order
                invoices = self.env['account.invoice'].sudo().search(domain_invoices, order='date asc, number asc') #facturas electronicas
                begin = row
                row += 1
                data_invoice = self.set_data_for_excel(sheet, row, invoices, taxes_title, titles, formats, exempt=False, employee_fee=True)
                #OKKKKK
                invoice_total = data_invoice.get('total').get('total')
                invoice_net = data_invoice.get('total').get('net')
                invoice_tax = data_invoice.get('total').get('reten')
                sheet = data_invoice['sheet']
                row = data_invoice['row']
                count_invoice += data_invoice['count_invoice']
                
                net_total = invoice_net 
                tax_total = invoice_tax
                total_total = invoice_total
                net_tax_total = net_total
                sheet.write(row + 3, col + 4, 'Total General', formats['title'])
                sheet.write(row + 3, col + 5, count_invoice, formats['total']) #SUMA DOCUMENTOS
                # sheet.write(row + 3, col + 7, exempt_total, formats['total'])
                # sheet.write(row + 3, col + 8, net_tax_total, formats['total'])
                sheet.write(row + 3, col + 6, net_total, formats['total'])
                sheet.write(row + 3, col + 7, tax_total, formats['total'])
                # sheet.write(row + 3, col + 11, 0, formats['total']) #TODO totoales iva no recuperable
                sheet.write(row + 3, col + 8, total_total, formats['total'])
        worksheet.autofit()
        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Libro de Honorarios {} {}.xlsx'.format(company_name, date.today().strftime("%d/%m/%Y"))
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': file_name,
            'datas_fname': file_name,
            'datas': file_base64
        })

        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'current',
        }
        return action
    
    def set_data_invoice(self, sheet, col, row, inv, invoices, taxes_title, titles, formats):
        # _logger.info('LOG: -- fact %r neto %r iva %r', inv, inv.amount_untaxed, inv.amount_tax)
        sheet.write(row, col, inv.document_class_id.sii_code if inv.document_class_id else inv.dte_code, formats['string'])
        col += 1
        # if inv.dte_folio:
        #     sheet.write(row, col, inv.dte_folio, formats['string'])
        #TODO esto es lo que debiera ir
        if inv.sii_document_number:
            sheet.write(row, col, inv.sii_document_number, formats['string'])
        else:
            sheet.write(row, col,'BH '+ inv.reference, formats['string'])
        # if inv.reference:
        #     sheet.write(row, col, inv.reference, formats['string'])
        # col += 1
        # if inv.number:
        #     long_folio = len(str(max(inv.mapped('number')))) + 6
        #     sheet.set_column(col, col, long_folio)
        #     sheet.write(row, col, inv.number, formats['string'])
        col += 1
        if inv.date:
            long_date = len(str(max(inv.mapped('date')))) + 3
            sheet.set_column(col, col, long_date)
            sheet.write(row, col, inv.date.strftime('%Y-%m-%d'), formats['string'])
        col += 1
        if inv.partner_id.document_number:
            long_vat = len(str(max(inv.mapped('partner_id').mapped('document_number')))) + 3
            sheet.set_column(col, col, long_vat)
            sheet.write(row, col, inv.partner_id.document_number, formats['string'])
        else:
            sheet.write(row, col, inv.partner_id.client_identifier_value, formats['string'])
        col += 1
        long_name = len(inv.partner_id.display_name) + 10
        sheet.set_column(col, col, long_name)
        sheet.write(row, col, inv.partner_id.display_name, formats['folio'])
        col += 2

        # exempt_taxes = inv.invoice_line_ids.filtered(lambda a: a.sii_code == 0 and a.amount == 0.0)
        # affect_taxes = inv.invoice_line_ids.filtered(lambda a: a.sii_code == 14)

        exempt_taxes = inv.invoice_line_ids.filtered(lambda a: 'Exento' in a.invoice_line_tax_ids.mapped('name') or 'Exento - Venta' in a.invoice_line_tax_ids.mapped('name') or len(a.invoice_line_tax_ids) == 0)

        affect_taxes = inv.invoice_line_ids.filtered(lambda a: 'IVA Débito' in a.invoice_line_tax_ids.mapped('name')) or inv.invoice_line_ids.filtered(lambda a: 'IVA Crédito' in a.invoice_line_tax_ids.mapped('name'))
        employee_fee_taxes = inv.invoice_line_ids.filtered(lambda a: 'Retención Boleta Honorarios' in a.invoice_line_tax_ids.mapped('name'))

        long_numbers = 17
        if exempt_taxes:
            _logger.info('LOG .>:::__ exento')
            sheet.set_column(col, col, long_numbers)
            exempt_sum = 0
            for f in exempt_taxes:
                exempt_sum += f.get_price_subtotal()

            sheet.write(row, col, exempt_sum, formats['number'])
            col += 1
            net = abs(inv.get_amount_untaxed())
            net_tax = inv.get_amount_neto()
            sheet.set_column(col, col, long_numbers)
            sheet.write(row, col, net_tax, formats['number'])
            col += 1
            
            if inv.document_class_id.id:
                sheet.set_column(col, col, long_numbers)
                sheet.write(row, col, inv.get_amount_untaxed(), formats['number'])
                col += 1
                sheet.set_column(col, col, long_numbers)
                sheet.write(row, col, inv.get_amount_tax(), formats['number'])
                col += 1
                sheet.set_column(col, col, long_numbers)
                sheet.write(row, col, '0', formats['number'])
                col += 1
                for tax in taxes_title:
                    if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                        line = inv.tax_line_ids.filtered(
                            lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
                                a.tax_id.name) == tax).mapped(
                            'amount')
                        sheet.set_column(col, col, long_numbers)
                        sheet.write(row, col, sum(line), formats['number'])
                        col += 1
                sheet.set_column(col, col, long_numbers)
                sheet.write(row, col, abs(inv.get_amount_total_signed()), formats['number'])
            else:
                sheet.set_column(col, col, long_numbers)
                sheet.write(row, col, sum(inv.invoice_line_ids.filtered(inv.invoice_line_ids.filtered(
                    lambda a: 'Exento' not in a.invoice_line_tax_ids.mapped('name') or 'Exento - Venta' in a.invoice_line_tax_ids.mapped('name') or len(
                        a.invoice_line_tax_ids) != 0)).mapped('price_subtotal')), formats['number'])
                col += 1
                sheet.set_column(col, col, long_numbers)
                sheet.write(row, col, sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
                            formats['number'])
                col += 1
                sheet.set_column(col, col, long_numbers)
                sheet.write(row, col, '0', formats['number'])
                col += 1
                for tax in taxes_title:
                    if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                        line = inv.tax_line_ids.filtered(
                            lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
                                a.tax_id.name) == tax).mapped(
                            'amount')
                        sheet.set_column(col, col, long_numbers)
                        sheet.write(row, col, sum(line), formats['number'])
                        col += 1
                sheet.set_column(col, col, long_numbers)
                sheet.write(row, col, abs(inv.amount_total_signed), formats['number'])
        elif affect_taxes:
            _logger.info('LOG .>:::__ afecto')
            sheet.set_column(col, col, long_numbers)
            sheet.write_number(row, col, 0, formats['number'])
            col += 1
            # sheet.write(row, col, inv.amount_untaxed_signed, formats['number'])
            net_tax = inv.amount_untaxed - abs(sum(exempt_taxes.mapped('price_subtotal')))
            sheet.set_column(col, col, long_numbers)
            sheet.write(row, col, net_tax, formats['number'])
            col += 1
            sheet.set_column(col, col, long_numbers)
            sheet.write(row, col, inv.amount_untaxed, formats['number']) ##Neto
            col += 1
            days = self.diff_dates(inv.date, date.today())
            if days <= 90:
                sheet.set_column(col, col, long_numbers)
                sheet.write(row, col,
                            sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
                            formats['number'])
                col += 1
                sheet.set_column(col, col, long_numbers)
                sheet.write_number(row, col, 0, formats['number'])
                col += 1
            else:
                sheet.set_column(col, col, long_numbers)
                sheet.write_number(row, col, 0, formats['number'])
                col += 1
                # sheet.write(row, col, inv.amount_tax, formats['number'])
                sheet.set_column(col, col, long_numbers)
                sheet.write(row, col,
                            sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
                            formats['number'])
                col += 1
            # for tax in taxes_title:
            #     if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
            #         line = inv.tax_line_ids.filtered(
            #             lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(a.tax_id.name) == tax).mapped(
            #             'amount')
            #         sheet.write(row, col, sum(line), formats['number'])
            #         col += 1
            sheet.set_column(col, col, long_numbers)
            sheet.write(row, col, abs(inv.amount_total_signed), formats['number'])
        elif employee_fee_taxes:
            sheet.set_column(col, col, long_numbers)
            sheet.write_number(row, col, int(inv.amount_untaxed), formats['number'])
            col += 1
            # sheet.write(row, col, inv.amount_untaxed_signed, formats['number'])
            # net_tax = inv.amount_untaxed - abs(sum(exempt_taxes.mapped('price_subtotal')))
            sheet.set_column(col, col, long_numbers)
            sheet.write(row, col, int(inv.amount_retencion), formats['number'])
            # sheet.write(row, col, int(inv.amount_tax), formats['number'])
            col += 1
            sheet.set_column(col, col, long_numbers)
            sheet.write(row, col, int(inv.amount_total_signed), formats['number']) ##Neto
            col += 1
            # days = self.diff_dates(inv.date, date.today())
            # if days <= 90:
            #     sheet.write(row, col,
            #                 sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
            #                 formats['number'])
            #     col += 1
            #     sheet.write_number(row, col, 0, formats['number'])
            #     col += 1
            # else:
            #     sheet.write_number(row, col, 0, formats['number'])
            #     col += 1
            #     # sheet.write(row, col, inv.amount_tax, formats['number'])
            #     sheet.write(row, col,
            #                 sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
            #                 formats['number'])
            #     col += 1
            # for tax in taxes_title:
            #     if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
            #         line = inv.tax_line_ids.filtered(
            #             lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(a.tax_id.name) == tax).mapped(
            #             'amount')
            #         sheet.write(row, col, sum(line), formats['number'])
            #         col += 1
            # sheet.write(row, col, abs(inv.amount_total_signed), formats['number'])
