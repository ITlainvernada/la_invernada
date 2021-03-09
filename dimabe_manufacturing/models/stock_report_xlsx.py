from odoo import fields, models, api
import xlsxwriter
from datetime import date
import base64
import datetime


class StockReportXlsx(models.TransientModel):
    _name = 'stock.report.xlsx'

    year = fields.Integer('Cosecha')

    @api.multi
    def generate_excel_raw_report(self):
        file_name = 'temp_report.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        sheet = workbook.add_worksheet('Informe de Materia Prima')
        row = 0
        col = 0
        titles = [(1, 'Productor:'), (2, 'Lote:'), (3, 'Kilos Disponible:'), (4, 'Variedad:'), (5, 'Calibre:'),
                  (6, 'Ubicacion Sistema:'), (7, 'Producto:'), (8, 'N° Guia:'), (9, 'Año Cosecha:'),
                  (10, 'Kilos Recepcionados:'), (11, 'Fecha Creacion:'), (12, 'Series Disponible:'),
                  (13, 'Enviado a Proceso de:'), (14, 'Fecha de Envio:'), (15, 'Ubicacion Fisica:'),
                  (16, 'Observaciones:')]
        for title in titles:
            sheet.write(row, col, title[1])
            col += 1
        row += 1
        col = 0

        lots = self.env['stock.production.lot'].sudo().search(
            [('product_id.categ_id.name', 'in', ('Seca', 'Desp. y Secado'))])
        for lot in lots:
            if lot.producer_id:
                sheet.write(row, col, lot.producer_id.display_name)
            else:
                sheet.write(row, col, "Sin Definir")
            col += 1
            sheet.write(row, col, lot.name)
            col += 1
            sheet.write(row, col, str(round(
                sum(lot.stock_production_lot_serial_ids.filtered(lambda a: not a.consumed).mapped(
                    'calculated_weight')),
                2)) if not lot.stock_production_lot_serial_ids.filtered(lambda a: not a.consumed).mapped(
                'display_weight') else str(round(
                sum(lot.stock_production_lot_serial_ids.filtered(lambda a: not a.consumed).mapped(
                    'display_weight')),
                2)))
            col += 1
            sheet.write(row, col, lot.product_id.get_variety())
            col += 1
            sheet.write(row, col, lot.product_id.get_calibers())
            col += 1
            if lot.location_id:
                sheet.write(row, col, lot.location_id.display_name)
            col += 1
            sheet.write(row, col, lot.product_id.display_name)
            col += 1
            sheet.write(row, col, lot.show_guide_number)
            col += 1
            sheet.write(row, col, lot.harvest)
            col += 1
            sheet.write(row, col, lot.reception_weight)
            col += 1
            sheet.write(row, col, lot.create_date.strftime("%d-%m-%Y %H:%M:%S"))
            col += 1
            sheet.write(row, col, len(lot.stock_production_lot_serial_ids.filtered(lambda a: not a.consumed)))
            col += 1
            if lot.workcenter_id:
                sheet.write(row, col, lot.workcenter_id.display_name)
            col += 1
            if lot.delivered_date:
                sheet.write(row, col, lot.delivered_date.strftime("%d-%m-%Y"))
            col += 1
            if lot.physical_location:
                sheet.write(row, col, lot.physical_location)
            col += 1
            if lot.observations:
                sheet.write(row, col, lot.observations)
            row += 1
            col = 0
        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        report_name = f'Informe de Existencia Materia Prima {date.today().strftime("%d/%m/%Y")}.xlsx'
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': report_name,
            'datas_fname': report_name,
            'datas': file_base64
        })

        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'current',
        }
        return action

    @api.multi
    def generate_excel_serial_report(self):
        file_name = 'temp_name.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        sheet = workbook.add_worksheet("Informe de Calibrado")
        row = 0
        col = 0
        titles = [(1, 'Productor:'), (2, 'Serie:'), (3, 'Kilos Disponibles:'), (4, 'Variedad:'), (5, 'Calibre:'),
                  (6, 'Ubicacion Sistema:'), (7, 'Producto:'), (8, 'Serie Disponible:'), (9, 'Fecha de Produccion:'),
                  (10, 'Cliente o Calidad:'), (11, 'Enviado a proceso:'), (12, 'Fecha de Envio:'),
                  (13, 'Ubicacion Fisica:'), (14, 'Observacion')]
        for title in titles:
            sheet.write(row, col, title[1])
            col += 1
        col = 0
        row += 1
        serials = self.env['stock.production.lot.serial'].sudo().search([('product_id.default_code', 'like', 'PSE006')])
        for serial in serials:
            sheet.write(row, col, serial.producer_id.display_name)
            col += 1
            sheet.write(row, col, serial.serial_number)
            col += 1
            sheet.write(row, col, serial.display_weight)
            col += 1
            sheet.write(row, col, serial.product_id.get_variety())
            col += 1
            sheet.write(row, col, serial.product_id.get_calibers())
            col += 1
            sheet.write(row, col, serial.stock_production_lot_id.location_id.display_name)
            col += 1
            sheet.write(row, col, serial.product_id.display_name)
            col += 1
            sheet.write(row, col, serial.consumed)
            col += 1
            sheet.write_datetime(row, col,
                                 datetime.datetime.combine(serial.packaging_date, datetime.datetime.min.time()))
            col += 1
            row += 1
            col = 0
        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        report_name = f'Informe de Existencia Producto Calibrado {date.today().strftime("%d/%m/%Y")}.xlsx'
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': report_name,
            'datas_fname': report_name,
            'datas': file_base64
        })

        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'current',
        }
        return action
