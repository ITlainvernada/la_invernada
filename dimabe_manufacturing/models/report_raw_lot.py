import base64
from datetime import date

import xlsxwriter

from odoo import fields, models, api


class ReportRawLot(models.Model):
    _name = 'report.raw.lot'
    _description = 'Reporte de materia primas'
    _rec_name = 'lot_id'
    _order = 'date ASC'

    lot_id = fields.Many2one('stock.production.lot', string='Lote')

    producer_id = fields.Many2one('res.partner', string='Productor')

    available_weight = fields.Float('Kilos disponibles')

    product_id = fields.Many2one('product.product', string='Producto')

    product_variety = fields.Char('Variedad')

    product_caliber = fields.Char('Calibre')

    location_id = fields.Many2one('stock.location', string='Ubicación')

    guide_number = fields.Char('N° de guia')

    lot_harvest = fields.Char('Cosecha')

    reception_weight = fields.Float('Kilos recepcionados')

    available_series = fields.Integer('Serie disponible')

    date = fields.Datetime('Fecha')

    send_to_process_id = fields.Many2one('mrp.workcenter', 'Enviado a proceso de')

    send_date = fields.Date('Fecha de envio')

    warehouse = fields.Char('Bodega')

    street = fields.Char('Calle')

    packaging_qty = fields.Integer('Cantidad de envases')

    position = fields.Char('Posición')

    available_date = fields.Date('Fecha disp.')

    observations = fields.Char('Observaciones')

    storage_warehouse = fields.Char('Bod. Alm.')

    origin_process = fields.Char('Proceso de origen')

    # TODO Eliminar luego de su implementacion
    def set_raw_lot(self):
        lot_ids = self.env['stock.production.lot'].sudo().search(
            [('product_id.default_code', 'ilike', 'MP'), ('product_id.default_code', 'not ilike', 'MPS'),
             ('product_id.name', 'not ilike', 'Verde'), ('stock_production_lot_serial_ids', '!=', False)])
        for lot in lot_ids:
            self.env[self._name].sudo().create({
                'lot_id': lot.id,
                'producer_id': lot.producer_id.id,
                'product_id': lot.product_id.id,
                'available_weight': sum(serial.display_weight for serial in
                                        lot.stock_production_lot_serial_ids.filtered(lambda x: not x.consumed)),
                'product_variety': lot.product_id.get_variety(),
                'product_caliber': lot.product_id.get_calibers(),
                'location_id': lot.location_id.id,
                'guide_number': lot.show_guide_number,
                'lot_harvest': lot.harvest,
                'reception_weight': lot.reception_weight,
                'date': lot.show_date,
                'available_series': len(lot.stock_production_lot_serial_ids.filtered(lambda x: not x.consumed)),
                'send_to_process_id': lot.workcenter_id.id,
                'send_date': lot.delivered_date,
                'available_date': lot.ventilation_date,
                'observations': lot.observations,
                'origin_process': lot.origin_process,
            })

    def get_format(self, type, workbook):
        format_excel = workbook.add_format()
        format_excel.set_text_wrap()
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
            format_excel.set_num_format('dd-mm-yyyy')
        if type == 'text':
            format_excel.set_border(1)
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
        return format_excel

    def export_to_xlsx(self, harvest):
        file_name = 'C:\\Users\\fabia\\Documents\\test.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        sheet = workbook.add_worksheet('Informe de materia prima')
        row = col = 0
        titles = ['Productor', 'Lote', 'Kilos disponible', 'Variedad', 'Calibre', 'Ubicacion del sistema', 'Producto',
                  'N° Guia', 'Año de cosecha', 'Kilos recepcionados', 'Fecha de creación', 'Series disponibles',
                  'Enviado a proceso de ', 'Fecha de envio', 'Bodega', 'Calle', 'Cantidad de envases', 'Posición',
                  'Fecha disp.',
                  'Observaciones', 'Bod.Almacenamiento']
        for title in titles:
            sheet.write(row, col, title, self.get_format('header', workbook))
            col += 1
        row += 1
        col = 0
        raw_lot_ids = self.env[self._name].sudo().search([('lot_harvest', '=', harvest)])
        for r_lot in raw_lot_ids:
            sheet.write(row, col, r_lot.producer_id.display_name, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, r_lot.lot_id.name, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, r_lot.available_weight, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, r_lot.product_variety, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, r_lot.product_caliber, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, r_lot.location_id.display_name, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, r_lot.product_id.display_name, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, r_lot.guide_number, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, r_lot.lot_harvest, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, r_lot.reception_weight, self.get_format('text', workbook))
            col += 1
            sheet.write(row, col, r_lot.date, self.get_format('datetime', workbook))
            col += 1
            sheet.write(row, col, r_lot.available_series, self.get_format('text', workbook))
            col += 1
            if r_lot.send_to_process_id:
                sheet.write(row, col, r_lot.send_to_process_id.display_name, self.get_format('text', workbook))
            else:
                sheet.write(row, col, '', self.get_format('text', workbook))
            col += 1
            if r_lot.send_date:
                sheet.write(row, col, r_lot.send_date, self.get_format('datetime', workbook))
            else:
                sheet.write(row, col, '', self.get_format('text', workbook))
            col += 1
            if r_lot.warehouse:
                sheet.write(row, col, r_lot.warehouse, self.get_format('text', workbook))
            else:
                sheet.write(row, col, '', self.get_format('text', workbook))
            col += 1
            if r_lot.street:
                sheet.write(row, col, r_lot.street, self.get_format('text', workbook))
            else:
                sheet.write(row, col, '', self.get_format('text', workbook))
            col += 1
            if r_lot.packaging_qty > 0:
                sheet.write(row, col, r_lot.packaging_qty, self.get_format('text', workbook))
            else:
                sheet.write(row, col, '', self.get_format('text', workbook))
            col += 1
            if r_lot.position:
                sheet.write(row, col, r_lot.position, self.get_format('text', workbook))
            else:
                sheet.write(row, col, '', self.get_format('text', workbook))
            col += 1
            if r_lot.available_date:
                sheet.write(row, col, r_lot.available_date, self.get_format('datetime', workbook))
            else:
                sheet.write(row, col, '', self.get_format('text', workbook))
            col += 1
            if r_lot.observations:
                sheet.write(row, col, r_lot.observations, self.get_format('datetime', workbook))
            else:
                sheet.write(row, col, '', self.get_format('text', workbook))
            col += 1
            if r_lot.storage_warehouse:
                sheet.write(row, col, r_lot.storage_warehouse, self.get_format('datetime', workbook))
            else:
                sheet.write(row, col, '', self.get_format('text', workbook))

            col = 0
            row += 1
        sheet.autofit()
        workbook.close()
        with open(file_name, 'rb') as file:
            file_base64 = base64.b64encode(file.read())
        report_name = f'Informe de existencia materia prima {date.today().strftime("%d/%m/%Y")}.xlsx'
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': report_name,
            'datas_fname': report_name,
            'datas': file_base64
        })

        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'new',
        }
        return action

    def generate_new_position(self):
        for item in self:
            original = self.env['report.raw.lot'].sudo().search([('lot_id', '=', item.lot_id.id)], limit=1)
            self.env['report.raw.lot'].sudo().create({
                'lot_id': item.lot_id.id,
                'producer_id': item.producer_id.id,
                'product_id': item.product_id.id,
                'available_weight': item.available_weight if not original else 0,
                'product_variety': item.product_variety,
                'product_caliber': item.product_caliber,
                'location_id': item.location_id.id,
                'guide_number': item.guide_number,
                'lot_harvest': item.lot_harvest,
                'date': item.date,
                'reception_weight': item.reception_weight if not original else 0,
                'available_series': item.available_series if not original else 0,
            })

    def delete_position(self):
        for item in self:
            lot_id = item.lot_id.id
            item.unlink()
            if lot_id:
                report_id = self.env['report.raw.lot'].sudo().search(
                    [('lot_id', '=', lot_id)], limit=1, order='create_date ASC')
                if report_id:
                    report_id.manage_report()

    @api.model
    def create(self, vals_list):
        res = super(ReportRawLot, self).create(vals_list)
        res.origin_process = res.lot_id.origin_process
        return res
    
    def manage_report(self, lot_id=None):
        if lot_id:
            lot = self.env['stock.production.lot'].sudo().search([('id', '=', lot_id)])
            self.env[self._name].sudo().create({
                'lot_id': lot.id,
                'producer_id': lot.producer_id.id,
                'product_id': lot.product_id.id,
                'available_weight': sum(serial.display_weight for serial in
                                        lot.stock_production_lot_serial_ids.filtered(lambda x: not x.consumed)),
                'product_variety': lot.product_id.get_variety(),
                'product_caliber': lot.product_id.get_calibers(),
                'location_id': lot.location_id.id,
                'guide_number': lot.show_guide_number,
                'lot_harvest': lot.harvest,
                'reception_weight': lot.reception_weight,
                'date': lot.show_date,
                'available_series': len(lot.stock_production_lot_serial_ids.filtered(lambda x: not x.consumed)),
                'send_to_process_id': lot.workcenter_id.id,
                'send_date': lot.delivered_date
            })
        else:
            lot = self.lot_id
            original = self.env['report.raw.lot'].sudo().search([('lot_id.id', '=', lot.id)], limit=1,
                                                                order='create_date asc')
            self.sudo().write({
                'lot_id': lot.id,
                'producer_id': lot.producer_id.id,
                'product_id': lot.product_id.id,
                'available_weight': sum(serial.display_weight for serial in
                                        lot.stock_production_lot_serial_ids.filtered(
                                            lambda x: not x.consumed)) if original and original.id == self.id else 0,
                'product_variety': lot.product_id.get_variety(),
                'product_caliber': lot.product_id.get_calibers(),
                'location_id': lot.location_id.id,
                'guide_number': lot.show_guide_number,
                'lot_harvest': lot.harvest,
                'reception_weight': lot.reception_weight if original and original.id == self.id else 0,
                'date': lot.show_date,
                'available_series': len(
                    lot.stock_production_lot_serial_ids.filtered(
                        lambda x: not x.consumed)) if original.id and original.id == self.id else 0,
                'send_to_process_id': lot.workcenter_id.id,
                'send_date': lot.delivered_date
            })

    def delete_duplicate(self, harvest):
        lot_ids = self.env['stock.production.lot'].sudo().search(
            [('product_id.default_code', 'ilike', 'MP'), ('product_id.default_code', 'not ilike', 'MPS'),
             ('product_id.name', 'not ilike', 'Verde'), ('stock_production_lot_serial_ids', '!=', False),
             ('harvest', '=', harvest)])
        for lot in lot_ids:
            lot.sudo().write({
                'available_kg': sum(serial.display_weight for serial in
                                    lot.stock_production_lot_serial_ids.filtered(lambda x: not x.consumed))
            })
            try:
                raw_ids = self.env['report.raw.lot'].sudo().search([('lot_id.id', '=', lot.id)])
                if len(raw_ids.filtered(lambda x: not x.position)) > 1:
                    raw_ids[1:].unlink()
                for raw in raw_ids:
                    raw.manage_report()
            except Exception as e:
                continue

