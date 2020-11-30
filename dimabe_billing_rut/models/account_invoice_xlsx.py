from odoo import fields , models , api
import base64
import csv
import datetime
import io
import logging
import time
from datetime import datetime,date
import xlsxwriter
from dateutil import relativedelta

class AccountInvoiceXlsx(models.Model):
    _name = 'account.invoice.xlsx'

    report_file = fields.Binary("Libro de Compra",default=lambda self: self.env['account.invoice.xlsx'].search([])[-1].report_file)

    report_name = fields.Char("Reporte")

    both = fields.Boolean("Ambas")

    @api.multi
    def generate_book(self):
        for item in self:
            file_name = 'temp'
            array_worksheet = []
            today = date.today()
            companies = self.env['res.company'].search([('add_to_sale_book','=',True)],order='id asc')
            workbook = xlsxwriter.Workbook(file_name,{'in_memory':True})
            for com in companies:
                worksheet = workbook.add_worksheet(com.display_name)
                array_worksheet.append({'company_name':com.display_name,'company_id':com.id,'worksheet':worksheet})
            for wk in array_worksheet:
                sheet = wk['worksheet']
                merge_format_string = workbook.add_format({
                    'border': 0,
                    'align': 'center',
                    'valign': 'vcenter',
                })
                merge_format_title = workbook.add_format({
                    'bold': 1,
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter',
                })
                company = self.env['res.company'].search([('id','=',wk['company_id'])])
                region = self.env['region.address'].search([('id','=',1)])
                sheet.merge_range('A1:C1',wk['company_name'],merge_format_string)
                sheet.merge_range('A2:C2',company.vat,merge_format_string)
                sheet.merge_range('A3:C3','{}, Region {}'.format(company.city,region.name.capitalize()),merge_format_string)
                sheet.merge_range('A5:L5', 'Libro de Compras',
                                  merge_format_title)
                sheet.merge_range('A6:L6', 'Libro de Compras Ordenado Por fecha	',merge_format_string)
                sheet.write('K7','Fecha:',merge_format_string)
                sheet.write('L7',today.strftime("%d-%m-%Y"),merge_format_string)
            workbook.close()
            with open(file_name, "rb") as file:
                file_base64 = base64.b64encode(file.read())
            self.write({'report_file': file_base64, 'report_name': 'Libro de Ventas'})
            return {
                "type": "ir.actions.do_nothing",
            }