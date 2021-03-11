import base64
from datetime import date
import string
import xlsxwriter
from odoo import fields, models, api
from collections import Counter


class AccountInvoiceXlsx(models.Model):
    _name = 'account.invoice.xlsx'

    purchase_file = fields.Binary(
        "Libro de Compra")

    company_get_id = fields.Many2one('res.company', 'Compañia')

    purchase_report_name = fields.Char("Reporte Compra",
                                       )

    sale_file = fields.Binary(
        "Libro de Venta")

    sale_report_name = fields.Char("Reporte Venta")

    from_date = fields.Date('Desde')

    to_date = fields.Date('Hasta')

    both = fields.Boolean("Ambas")

    @api.multi
    def generate_sale_book(self):
        for item in self:
            file_name = 'salebook.xlsx'
            array_worksheet = []
            companies = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            workbook = xlsxwriter.Workbook(file_name, {'in_memory': True, 'strings_to_numbers': True})
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
                formats = self.set_formats(workbook)
                region = self.env['region.address'].search([('id', '=', 1)])
                titles = ['Cod.SII', 'Folio', 'Cor.Interno', 'Fecha', 'RUT', 'Nombre', '#', 'EXENTO', 'NETO', 'IVA',
                          'IVA NO RECUPERABLE']
                invoices_get_tax = self.env['account.invoice'].sudo().search([('dte_type_id', '!=', None)])
                taxes_title = list(
                    dict.fromkeys(invoices_get_tax.mapped('tax_line_ids').mapped('tax_id').mapped('name')))
                for tax in taxes_title:
                    if tax != 'IVA Crédito' and tax != 'IVA Débito' and tax != 'Exento':
                        titles.append(tax.upper())

                titles.append('Total')
                sheet.merge_range(0, 0, 0, 2, self.company_get_id.display_name, formats['title'])
                sheet.merge_range(1, 0, 1, 2, self.company_get_id.invoice_rut, formats['title'])
                sheet.merge_range(2, 0, 2, 2,
                                  f'{self.company_get_id.city},Region {self.company_get_id.region_address_id.name}',
                                  formats['title'])
                sheet.merge_range(4, 3, 4, 6, 'Libro de Ventas', formats['title'])
                sheet.merge_range(5, 3, 5, 6, 'Libro de Ventas Ordenado por fecha', formats['title'])
                sheet.write(6, 10, 'Fecha', formats['title'])
                sheet.write(6, 11, date.today().strftime('%Y-%m-%d'), formats['title'])
                sheet.merge_range(6, 3, 6, 6, f'Desde {self.from_date} Hasta {self.to_date}', formats['title'])
                sheet.merge_range(7, 3, 7, 6, 'Moneda : Peso Chileno', formats['title'])
                row = 12
                col = 0
                for title in titles:
                    sheet.write(row, col, title, formats['title'])
                    col += 1
                row += 2
                col = 0
                sheet.merge_range(row, col, row, 5, 'Factura de venta electronica. (FACTURA VENTA  ELECTRONICA)',
                                  formats['title'])
                row += 1
                invoices = self.env['account.invoice'].sudo().search(
                    [('date_invoice', '>', self.from_date),
                     ('type', 'in', ('in_invoice', 'in_refund')),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 33),
                     ('company_id.id', '=', self.company_get_id.id)])
                begin = row
                row += 1
                data_invoice = self.set_data_for_excel(sheet, row, invoices, taxes_title, titles, formats,exempt=False)
                sheet = data_invoice['sheet']
                row = data_invoice['row']
                exempts = self.env['account.invoice'].sudo().search([('date_invoice', '>', self.from_date),
                                                                     ('type', 'in', ('in_invoice', 'in_refund')),
                                                                     ('date_invoice', '<', self.to_date),
                                                                     ('dte_type_id.code', '=', 34),
                                                                     ('company_id.id', '=', self.company_get_id.id)])
                row += 2
                sheet.merge_range(row, col, row, 5,
                                  'Factura de venta exenta electronica. (FACTURA Venta ELECTRONICA)',
                                  formats['title'])
                row += 1
                data_exempt = self.set_data_for_excel(sheet, row, exempts, taxes_title, titles, formats, exempt=True)
                sheet = data_exempt['sheet']
                row = data_exempt['row']
                credit = self.env['account.invoice'].sudo().search([('date_invoice', '>', self.from_date),
                                                                    ('type', 'in', ('in_invoice', 'in_refund')),
                                                                    ('date_invoice', '<', self.to_date),
                                                                    ('dte_type_id.code', '=', 61),
                                                                    ('company_id.id', '=', self.company_get_id.id)])

                row += 2
                sheet.merge_range(row, col, row, 5, 'NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO VENTA ELECTRONICA)',
                                  formats['title'])
                row += 1
                data_credit = self.set_data_for_excel(sheet, row, credit, taxes_title, titles, formats,exempt=False)
                sheet = data_credit['sheet']
                row = data_credit['row']
                row += 2
                sheet.merge_range(row, col, row, 5, 'NOTA DE DEBITO ELECTRONICA (NOTA DE DEBITO VENTA ELECTRONICA)',
                                  formats['title'])
                row += 1
                debit = self.env['account.invoice'].sudo().search([('date_invoice', '>', self.from_date),
                                                                   ('date_invoice', '<', self.to_date),
                                                                   ('type', 'in', ('in_invoice', 'in_refund')),
                                                                   ('dte_type_id.code', '=', 56),
                                                                   ('company_id.id', '=', self.company_get_id.id)])
                data_debit = self.set_data_for_excel(sheet, row, debit, taxes_title, titles, formats,exempt=False)
                sheet = data_debit['sheet']
                row = data_debit['row']

        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Libro de Ventas {} {}.xlsx'.format(company_name, date.today().strftime("%d/%m/%Y"))
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

    @api.multi
    def generate_purchase_book(self):
        for item in self:
            file_name = 'salebook.xlsx'
            array_worksheet = []
            companies = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            workbook = xlsxwriter.Workbook(file_name, {'in_memory': True, 'strings_to_numbers': True})
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
                formats = self.set_formats(workbook)
                region = self.env['region.address'].search([('id', '=', 1)])
                titles = ['Cod.SII', 'Folio', 'Cor.Interno', 'Fecha', 'RUT', 'Nombre', '#', 'EXENTO', 'NETO', 'IVA',
                          'IVA NO RECUPERABLE']
                invoices_get_tax = self.env['account.invoice'].sudo().search([('dte_type_id', '!=', None)])
                taxes_title = list(
                    dict.fromkeys(invoices_get_tax.mapped('tax_line_ids').mapped('tax_id').mapped('name')))
                for tax in taxes_title:
                    if tax != 'IVA Crédito' and tax != 'IVA Débito' and tax != 'Exento':
                        titles.append(tax.upper())

                titles.append('Total')
                sheet.merge_range(0, 0, 0, 2, self.company_get_id.display_name, formats['title'])
                sheet.merge_range(1, 0, 1, 2, self.company_get_id.invoice_rut, formats['title'])
                sheet.merge_range(2, 0, 2, 2,
                                  f'{self.company_get_id.city},Region {self.company_get_id.region_address_id.name}',
                                  formats['title'])
                sheet.merge_range(4, 3, 4, 6, 'Libro de Ventas', formats['title'])
                sheet.merge_range(5, 3, 5, 6, 'Libro de Ventas Ordenado por fecha', formats['title'])
                sheet.write(6, 10, 'Fecha', formats['title'])
                sheet.write(6, 11, date.today().strftime('%Y-%m-%d'), formats['title'])
                sheet.merge_range(6, 3, 6, 6, f'Desde {self.from_date} Hasta {self.to_date}', formats['title'])
                sheet.merge_range(7, 3, 7, 6, 'Moneda : Peso Chileno', formats['title'])
                row = 12
                col = 0
                for title in titles:
                    sheet.write(row, col, title, formats['title'])
                    col += 1
                row += 2
                col = 0
                sheet.merge_range(row, col, row, 5, 'Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)',
                                  formats['title'])
                row += 1
                invoices = self.env['account.invoice'].sudo().search(
                    [('date_invoice', '>', self.from_date),
                     ('type', 'in', ('out_invoice', 'out_refund')),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 33),
                     ('company_id.id', '=', self.company_get_id.id)])
                begin = row
                row += 1
                data_invoice = self.set_data_for_excel(sheet, row, invoices, taxes_title, titles, formats,exempt=False)
                sheet = data_invoice['sheet']
                row = data_invoice['row']
                exempts = self.env['account.invoice'].sudo().search([('date_invoice', '>', self.from_date),
                                                                     ('type', 'in', ('out_invoice', 'out_refund')),
                                                                     ('date_invoice', '<', self.to_date),
                                                                     ('dte_type_id.code', '=', 34),
                                                                     ('company_id.id', '=', self.company_get_id.id)])
                row += 2
                sheet.merge_range(row, col, row, 5,
                                  'Factura de compra exenta electronica. (FACTURA COMPRA ELECTRONICA)',
                                  formats['title'])
                row += 1
                data_exempt = self.set_data_for_excel(sheet, row, exempts, taxes_title, titles, formats, exempt=True)
                sheet = data_exempt['sheet']
                row = data_exempt['row']
                credit = self.env['account.invoice'].sudo().search([('date_invoice', '>', self.from_date),
                                                                    ('type', 'in', ('out_invoice', 'out_refund')),
                                                                    ('date_invoice', '<', self.to_date),
                                                                    ('dte_type_id.code', '=', 61),
                                                                    ('company_id.id', '=', self.company_get_id.id)])

                row += 2
                sheet.merge_range(row, col, row, 5, 'NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)',
                                  formats['title'])
                row += 1
                data_credit = self.set_data_for_excel(sheet, row, credit, taxes_title, titles, formats,exempt=False)
                sheet = data_credit['sheet']
                row = data_credit['row']
                row += 2
                sheet.merge_range(row, col, row, 5, 'NOTA DE DEBITO ELECTRONICA (NOTA DE DEBITO COMPRA ELECTRONICA)',
                                  formats['title'])
                row += 1
                debit = self.env['account.invoice'].sudo().search([('date_invoice', '>', self.from_date),
                                                                   ('date_invoice', '<', self.to_date),
                                                                   ('type', 'in', ('out_invoice', 'out_refund')),
                                                                   ('dte_type_id.code', '=', 56),
                                                                   ('company_id.id', '=', self.company_get_id.id)])
                data_debit = self.set_data_for_excel(sheet, row, debit, taxes_title, titles, formats,exempt=False)
                sheet = data_debit['sheet']
                row = data_debit['row']

        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Libro de Compra {} {}.xlsx'.format(company_name, date.today().strftime("%d/%m/%Y"))
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

    def set_data_for_excel(self, sheet, row, invoices, taxes_title, titles, formats, exempt):
        for inv in invoices:
            col = 0
            data = self.set_data_invoice(sheet, col, row, inv, invoices, taxes_title, titles, formats)
            sheet = data['sheet']
            row = data['row']
            col = data['col']
            if inv.id == invoices[-1].id:
                row += 2
            else:
                row += 1
        sheet.merge_range(row, 0, row, 5, 'Totales:', formats['text_total'])
        col = 6
        sheet.write(row, col, len(invoices), formats['total'])
        col += 1
        sheet.write(row, col, sum(invoices.mapped('invoice_line_ids').filtered(
            lambda a: 'Exento' in a.invoice_line_tax_ids.mapped('name') or len(
                a.invoice_line_tax_ids) == 0).mapped('price_subtotal')), formats['total'])
        col += 1
        sheet.write(row, col, sum(invoices.mapped('amount_untaxed_signed')), formats['total'])
        col += 1
        sheet.write(row, col, sum(
            invoices.mapped('tax_line_ids').filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
                    formats['total'])
        col += 1
        sheet.write(row, col, 0, formats['total'])
        col += 1
        for tax in taxes_title:
            if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                line = invoices.mapped('tax_line_ids').filtered(
                    lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
                        a.tax_id.name) == tax).mapped(
                    'amount')
                sheet.write(row, col, sum(line), formats['total'])
                col += 1
        if exempt:
            sheet.write(row, col, '0', formats['total'])
        else:
            sheet.write(row, col, sum(invoices.mapped('invoice_line_ids').filtered(
                lambda a: 'Exento' not in a.invoice_line_tax_ids.mapped('name') or len(
                    a.invoice_line_tax_ids) != 0).mapped('price_subtotal')), formats['total'])
        col = 0
        return {'sheet': sheet, 'row': row}

    def set_data_invoice(self, sheet, col, row, inv, invoices, taxes_title, titles, formats):
        sheet.write(row, col, inv.dte_type_id.code, formats['string'])
        col += 1
        if inv.dte_folio:
            sheet.write(row, col, inv.dte_folio, formats['string'])
        col += 1
        if inv.number:
            sheet.write(row, col, inv.number, formats['string'])
        col += 1
        if inv.date_invoice:
            sheet.write(row, col, inv.date_invoice.strftime('%Y-%m-%d'), formats['string'])
        col += 1
        if inv.partner_id.invoice_rut:
            sheet.write(row, col, inv.partner_id.invoice_rut, formats['string'])
        col += 1
        long_name = max(invoices.mapped('partner_id').mapped('display_name'), key=len)
        sheet.set_column(col, col, len(long_name))
        sheet.write(row, col, inv.partner_id.display_name, formats['string'])
        col += 2

        taxes = inv.invoice_line_ids.filtered(
            lambda a: 'Exento' in a.invoice_line_tax_ids.mapped('name') or len(a.invoice_line_tax_ids) == 0)
        if taxes:
            sheet.write(row, col, sum(taxes.mapped('price_subtotal')), formats['number'])
            col += 1
            net = inv.amount_untaxed_signed
            if inv.dte_type_id.id:
                sheet.write(row, col, '0', formats['number'])
                col += 1
                sheet.write(row, col, '0', formats['number'])
                col += 1
                sheet.write(row, col, '0', formats['number'])
                col += 1
                for tax in taxes_title:
                    if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                        line = inv.tax_line_ids.filtered(
                            lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
                                a.tax_id.name) == tax).mapped(
                            'amount')
                        sheet.write(row, col, sum(line), formats['number'])
                        col += 1
                sheet.write(row, col, inv.amount_total_signed, formats['number'])
            else:
                sheet.write(row, col, sum(inv.invoice_line_ids.filtered(inv.invoice_line_ids.filtered(
                    lambda a: 'Exento' not in a.invoice_line_tax_ids.mapped('name') or len(
                        a.invoice_line_tax_ids) != 0)).mapped('price_subtotal')), formats['number'])
                col += 1
                sheet.write(row, col, sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
                            formats['number'])
                col += 1
                sheet.write(row, col, '0', formats['number'])
                col += 1
                for tax in taxes_title:
                    if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                        line = inv.tax_line_ids.filtered(
                            lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
                                a.tax_id.name) == tax).mapped(
                            'amount')
                        sheet.write(row, col, sum(line), formats['number'])
                        col += 1
                sheet.write(row, col, inv.amount_total_signed, formats['number'])
        else:
            sheet.write_number(row, col, 0, formats['number'])
            col += 1
            sheet.write(row, col, inv.amount_untaxed_signed, formats['number'])
            col += 1
            sheet.write(row, col,
                        sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
                        formats['number'])
            col += 1
            sheet.write_number(row, col, 0, formats['number'])
            col += 1
            for tax in taxes_title:
                if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                    line = inv.tax_line_ids.filtered(
                        lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(a.tax_id.name) == tax).mapped(
                        'amount')
                    sheet.write(row, col, sum(line), formats['number'])
                    col += 1
            sheet.write(row, col, inv.amount_total_signed, formats['number'])

        return {'sheet': sheet, 'row': row, 'col': col}

    def diff_dates(self, date1, date2):
        return abs(date2 - date1).days

    def get_another_taxes(self, inv):
        another = []
        for line in inv.mapped('invoice_line_ids'):

            if line.invoice_line_tax_ids and len(line.invoice_line_tax_ids) > 0:
                for tax in line.invoice_line_tax_ids:
                    if tax.amount != 19 and tax.amount > 0:
                        another.append(line)
        return another

    def set_formats(self, workbook):
        merge_format_string = workbook.add_format({
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
        })
        merge_format_number = workbook.add_format({
            'bold': 0,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0'
        })
        merge_format_title = workbook.add_format({
            'border': 1,
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        merge_format_total = workbook.add_format({
            'border': 1,
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0'
        })
        merge_format_total_text = workbook.add_format({
            'border': 1,
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        return {
            'string': merge_format_string,
            'number': merge_format_number,
            'title': merge_format_title,
            'total': merge_format_total,
            'text_total': merge_format_total_text
        }
