import base64
from datetime import datetime, timedelta
from odoo import models, fields
from pathlib import Path
from pytz import timezone
from dateutil import relativedelta
import xlsxwriter


class ReportCanningXlsx(models.TransientModel):
    _name = 'report.canning.xlsx'

    start_date = fields.Date('Fecha de inicio')

    end_date = fields.Date('Fecha de final')

    def generate_xlsx(self):
        file_name = 'C:\\Users\\fabia\\Documents\\test.xlsx'
        file_path = Path(file_name)
        file_path.touch(exist_ok=True)
        workbook = xlsxwriter.Workbook(file_name, {'strings_to_numbers': True})
        sheet = workbook.add_worksheet('Envases')
        titles = ['Productor', 'Codigo de envase', 'Nombre de envase', 'Cantidad de envases',
                  'Cantidad de Envases (Con simbolo)', 'Operación', 'N° de guía'
                                                                    'Tipo de operación',
                  'Fecha efectiva']
        row = col = 0
        for title in titles:
            sheet.write(row, col, title, self.get_format('header', workbook))
            col += 1
        sheet.autofilter(0, 0, 0, len(titles) - 1)
        canning_ids = self.env['stock.move.line'].sudo().search(
            [('picking_id.picking_type_id.show_in_canning_report', '=', True), ('state', '=', 'done'),
             ('product_id.categ_id.parent_id', '=', 95), ('picking_id.date_done', '>=', self.start_date),
             ('picking_id.date_done', '<=', self.end_date)])
        col = 0
        row += 1
        for canning in canning_ids:
            date_done = self.get_datetime_by_timezone(canning.picking_id.date_done, self.env.context['tz'])
            qty = canning.qty_done if canning.picking_id.picking_type_id.code == 'incoming' else -canning.qty_done
            guide_number = canning.picking_id.guide_number if canning.picking_id.picking_type_id.code == 'incoming' else canning.picking_id.name
            show_name = canning.product_id.name
            if len(canning.product_id.attribute_value_ids) > 0:
                attributes = canning.product_id.attribute_value_ids.mapped('display_name')
                show_name = f'{canning.product_id.name} ({",".join(attributes)})'

            sheet.write(row, col, canning.picking_id.partner_id.display_name, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, canning.product_id.default_code, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, show_name, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, canning.qty_done, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, qty, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, canning.picking_id.name, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, guide_number, self.get_format('text',workbook))
            col += 1
            sheet.write(row, col, 'Entrada' if canning.picking_id.picking_type_id.code == 'incoming' else 'Salida',
                        self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, date_done, self.get_format('datetime', workbook))
            row += 1
            col = 0
        sheet.autofit()
        workbook.close()
        with open(file_path, 'rb') as file:
            file_base64 = base64.b64encode(file.read())
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': f'Reporte de envases {fields.Date.to_string(self.start_date)} - {fields.Date.to_string(self.end_date)}.xlsx',
            'datas_fname': f'Reporte de envases {fields.Date.to_string(self.start_date)} - {fields.Date.to_string(self.end_date)}.xlsx',
            'datas': file_base64
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment_id.id}?download=true',
            'target': 'new'
        }

    def get_format(self, type, workbook):
        format_excel = workbook.add_format()
        if type == "header":
            format_excel.set_border(1)
            format_excel.set_bold()
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
        if type == "header_text":
            format_excel.set_border(1)
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
        if type == "money":
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_border(1)
            format_excel.set_border_color("black")
            format_excel.set_num_format('$#,##0')
        if type == "header_label":
            format_excel.set_align('center')
            format_excel.set_border(1)
            format_excel.set_align('vcenter')
        if type == 'title':
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_border(1)
            format_excel.set_bold()
            format_excel.set_bg_color("#0083be")
            format_excel.set_font_color("#FFFFFF")
        if type == 'total':
            format_excel.set_border(1)
            format_excel.set_bold()
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_bg_color("#0083be")
            format_excel.set_font_color("#FFFFFF")
        if type == 'total_money':
            format_excel.set_border(1)
            format_excel.set_bold()
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_bg_color("#0083be")
            format_excel.set_font_color("#FFFFFF")
            format_excel.set_num_format('$#,##0')
        if type == 'datetime':
            format_excel.set_border(1)
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_num_format('dd-mm-yyyy hh:mm')
        if type == 'text':
            format_excel.set_border(1)
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
        return format_excel

    def get_datetime_by_timezone(self, date, time_zone):
        current_timezone = timezone(time_zone)
        offset = current_timezone.utcoffset(date).total_seconds() / 3600
        return date - timedelta(hours=abs(offset))
