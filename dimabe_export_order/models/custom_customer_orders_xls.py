import base64
import datetime

import xlsxwriter
from odoo import fields, models, api


class CustomCustomerOrdersXls(models.TransientModel):
    _name = 'custom.customer.orders.xls'
    _description = "Generador de Archivo de Pedidos"

    orders_file = fields.Binary('Archivo de Pedidos')

    for_year = fields.Integer(string="Año")

    @api.multi
    def generate_orders_file_v2(self):
        file_name = 'temp.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        sheet = workbook.add_worksheet('Pedidos Clientes')
        row = 0
        col = 0
        titles = ['N° EMD', 'ETD', 'Sem ETD', 'Cargar Hasta', 'Sem Carga', 'Cliente', 'País', 'Contrato Interno',
                  'N° Pedido Odoo', 'N° Despacho Odoo', 'Estado Producción', 'Estatus Despacho', 'Estatus Producción',
                  'Estado A. Calidad', 'Envío al cliente', 'Especia', 'Variedad', 'Color', 'Producto', 'Calibre',
                  'Kilos', 'Kilos Entregados', 'Kilos facturados', 'Precio', 'Monto', 'N° Factura', 'Cláusula',
                  'Envase',
                  'Modo de carga', 'Etiqueta Cliente', 'Marca', 'Agente', 'Comisión', 'Valor Comisión',
                  'Puerto de Carga', 'Puerto de Destino', 'Destino final', 'Vía de transporte', 'Planta de carga',
                  'Fecha y Hora carga', 'N° de guía', 'Nave / Viajes', 'Naviera', 'N° Booking', 'N° BL', 'Stacking',
                  'Cut off Documental', 'F. Real Zarpe', 'F. Real arribo', 'N° Container', 'Tipo container',
                  'Terminal Portuario Origen', 'Despósito Retiro', 'Valor flete', 'Valor Seguro',
                  'Valor clausula total', ' FOB/Kg', 'Obs.Calidad', 'Comentarios', 'N° DUS'
                  ]
        for title in titles:
            sheet.write(row, col, title, self.get_format(workbook, 'title'))
            col += 1
        row += 1
        col = 0

        from_date = datetime.datetime(self.for_year, 1, 1)
        to_date = datetime.datetime(self.for_year, 12, 31)

        order_ids = self.env['sale.order'].sudo().search(
            [('create_date', '>=', from_date), ('create_date', '<=', to_date)])
        total_fob_per_kg = total_fob = total_safe = total_freight = total_container = total_bl = \
            total_commission = total_amount = total_kilogram = 0

        amount_total_invoice_ids = []
        other_fields_invoice_ids = []
        commission_invoice_ids = []

        if len(order_ids) > 0:
            for line in order_ids.mapped('order_line'):
                picking_ids = self.env['stock.picking'].sudo().search(
                    [('picking_type_id.code', '=', 'outgoing'), ('sale_id', '=', line.order_id.id),
                     ('state', '!=', 'cancel')], order='create_date desc', limit=1)
                for picking in picking_ids:
                    # invoice_line_ids = self.env['account.invoice.line'].sudo().search(
                    #     [('stock_picking_id', '=', picking.id)])
                    production = self.env['mrp.production']
                    if len(picking.packing_list_ids) > 0:
                        if len(picking.packing_list_ids.mapped('production_id')) > 0:
                            production = picking.packing_list_ids.mapped('production_id')
                    exist_account_invoice = False
                    account_invoice = self.env['account.invoice']
                    invoice_line_id = self.env['account.invoice.line'].sudo().search(
                        [('order_name', '=', line.order_id.name)], order='create_date desc', limit=1)
                    if invoice_line_id:
                        account_invoice = invoice_line_id.invoice_id
                        exist_account_invoice = True
                    sheet.write(row, col, picking.shipping_number if picking.shipping_number else '')
                    col += 1
                    if picking.etd:
                        sheet.write(row, col, picking.etd, self.get_format(workbook, 'date'))
                    col += 1
                    sheet.write(row, col, picking.etd_week, self.get_format(workbook))
                    col += 1
                    if picking.required_loading_date:
                        sheet.write(row, col, picking.required_loading_date, self.get_format(workbook, 'date'))
                    col += 1
                    sheet.write(row, col, picking.required_loading_week, self.get_format(workbook))
                    col += 1
                    if picking.partner_id:
                        sheet.write(row, col, picking.partner_id.name, self.get_format(workbook))
                    col += 1
                    if picking.partner_id.country_id:
                        sheet.write(row, col, picking.partner_id.country_id.name, self.get_format(workbook))
                    col += 1
                    if line.order_id.contract_number:
                        sheet.write(row, col, line.order_id.contract_number, self.get_format(workbook))
                    col += 1
                    if line.order_id.client_contract:
                        sheet.write(row, col, line.order_id.client_contract, self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, line.order_id.name, self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, picking.name)
                    col += 1
                    if production:
                        if len(production) == 1:
                            if production.state == 'planned':
                                sheet.write(row, col, 'Planeado', self.get_format(workbook, 'pink_status'))
                            elif production.state == 'done':
                                sheet.write(row, col, 'Realizado', self.get_format(workbook, 'green_status'))
                            elif production.state == 'progress':
                                sheet.write(row, col, 'En progreso', self.get_format(workbook, 'light_green_status'))
                            elif production.state == 'confirmed':
                                sheet.write(row, col, 'Confirmado', self.get_format(workbook, 'yellow_status'))
                            elif production.state == 'cancel':
                                sheet.write(row, col, 'Cancelado', self.get_format(workbook, 'red_status'))
                col = 0
                row += 1
        sheet.autofit()
        workbook.close()
        with open(file_name, 'rb') as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Archivo de Pedido - {}'.format(self.for_year)
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': file_name,
            'data_fname': file_name,
            'datas': file_base64
        })
        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id),
            'target': 'current'
        }
        return action

    def get_format(self, book, type=''):
        format_excel = book.add_format()
        format_excel.set_text_wrap()
        format_excel.set_align('center')
        format_excel.set_align('vcenter')
        if type == 'date':
            format_excel.set_num_format('dd-mm-yyyy')
        if type == 'number':
            format_excel.set_num_format('#,##0.00')
        if type == 'clp':
            format_excel.set_num_format('$ #,##0.00')
        if type == 'usd':
            format_excel.set_num_format('[$USD-409] #,##0.00')
        if type == 'euro':
            format_excel.set_num_format('€ #,##0.00')
        if type == 'title':
            format_excel.set_bold()
            format_excel.set_bg_color('#8064a2')
            format_excel.set_font_color('white')
        if type == 'title_number':
            format_excel.set_bold()
            format_excel.set_bg_color('#8064a2')
            format_excel.set_font_color('white')
            format_excel.set_num_format('#,##0.00')
        if type == 'red_status':
            format_excel.set_bg_color('#c30f0f')
            format_excel.set_font_color('white')
        if type == 'yellow_status':
            format_excel.set_bg_color('#ffeb9c')
            format_excel.set_font_color('black')
        if type == 'green_status':
            format_excel.set_bg_color('#87c842')
            format_excel.set_font_color('black')
        if type == 'pink_status':
            format_excel.set_bg_color('#ffc7ce')
            format_excel.set_font_color('#9c0031')
        return format_excel
