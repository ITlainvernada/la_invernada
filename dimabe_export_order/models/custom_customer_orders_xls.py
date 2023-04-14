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
        workbook = xlsxwriter.Workbook(file_name, {'strings_to_numbers': True})
        sheet = workbook.add_worksheet('Pedidos Clientes')
        row = 0
        col = 0
        titles = ['N° EMD', 'ETD', 'Sem ETD', 'Cargar Hasta', 'Sem Carga', 'Cliente', 'País', 'Contrato Interno'
            , 'Contrato Cliente',
                  'N° Pedido Odoo', 'N° Despacho Odoo', 'Estado Producción', 'Estatus Despacho',
                  'Estado A. Calidad', 'F. Envío al cliente', 'Especie', 'Variedad', 'Color', 'Producto', 'Calibre',
                  'Kilos', 'Kilos Entregados', 'Kilos facturados', 'Precio', 'Monto', 'Monto Facturado USD',
                  'N° Factura', 'Cláusula',
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
            [('create_date', '>=', from_date), ('create_date', '<=', to_date)], limit=20)
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
                    sheet.write(row, col, picking.name, self.get_format(workbook))
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
                        else:
                            status_type = []
                            for p in production:
                                if p.state not in status_type:
                                    status_type.append(p.state)
                            status_set = ' '.join(status_type)
                            sheet.write(row, col, status_set, self.get_format(workbook))
                    else:
                        sheet.write(row, col, 'Sin orden de producción', self.get_format(workbook))
                    col += 1
                    if exist_account_invoice:
                        if account_invoice.arrival_date:
                            sheet.write(row, col, 'Arribado', self.get_format(workbook))
                        else:
                            if picking.state == 'draft':
                                sheet.write(row, col, 'Borrador', self.get_format(workbook))
                            elif picking.state == 'assigned':
                                sheet.write(row, col, 'Asignado', self.get_format(workbook, 'pink_status'))
                            elif picking.state == 'confirmed':
                                sheet.write(row, col, 'Confirmado', self.get_format(workbook, 'yellow_status'))
                            elif picking.state == 'done':
                                sheet.write(row, col, 'Realizado', self.get_format(workbook, 'light_green_status'))
                            elif picking.state == 'cancel':
                                sheet.write(row, col, 'Cancelado', self.get_format(workbook, 'red_status'))
                    else:
                        if picking.state == 'draft':
                            sheet.write(row, col, 'Borrador', self.get_format(workbook))
                        elif picking.state == 'assigned':
                            sheet.write(row, col, 'Asignado', self.get_format(workbook, 'pink_status'))
                        elif picking.state == 'confirmed':
                            sheet.write(row, col, 'Confirmado', self.get_format(workbook, 'yellow_status'))
                        elif picking.state == 'done':
                            sheet.write(row, col, 'Realizado', self.get_format(workbook, 'light_green_status'))
                        elif picking.state == 'cancel':
                            sheet.write(row, col, 'Cancelado', self.get_format(workbook, 'red_status'))
                    col += 1

                    format_quality = ''
                    if picking.quality_status:
                        if picking.quality_status == 'Pendiente':
                            format_quality = 'pink_status'
                        elif picking.quality_status == 'Recibido':
                            format_quality = 'yellow_status'
                        elif picking.quality_status == 'Enviado':
                            format_quality = 'light_green_status'
                        elif picking.quality_status == 'Cancelado':
                            format_quality = 'red_status'
                        sheet.write(row, col, picking.quality_status, self.get_format(workbook, format_quality))
                    col += 1
                    if picking.shipping_date_to_customer:
                        sheet.write(row, col, picking.shipping_date_to_customer, self.get_format(workbook, 'date'))
                    col += 1
                    sheet.write(row, col, line.product_id.get_species(), self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, line.product_id.get_variety(), self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, line.product_id.get_color(), self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, line.product_id.name, self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, line.product_id.get_calibers(), self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, line.product_uom_qty, self.get_format(workbook, 'number'))
                    col += 1
                    sheet.write(row, col, line.qty_delivered, self.get_format(workbook, 'number'))
                    col += 1
                    sheet.write(row, col, line.qty_invoiced, self.get_format(workbook, 'number'))
                    col += 1
                    format_price = 'number_peso'
                    if line.currency_id.name == 'USD':
                        format_price = 'number_usd'
                    elif line.currency_id.name == 'EUR':
                        format_price = 'number_euro'
                    sheet.write(row, col, line.price_unit, self.get_format(workbook, format_price))
                    col += 1
                    sheet.write(row, col, line.price_subtotal, self.get_format(workbook, format_price))
                    col += 1
                    amount_in_usd = 0
                    usd = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
                    if usd == line.currency_id:
                        amount_in_usd = line.price_unit * line.qty_invoiced
                    else:
                        print()
                    sheet.write(row, col,amount_in_usd,self.get_format(workbook, 'number_usd'))
                    col += 1
                    if exist_account_invoice:
                        sheet.write(row, col, account_invoice.number if account_invoice.number else (
                            account_invoice.sii_document_number if account_invoice.sii_document_number else ''),
                                    self.get_format(workbook))
                    else:
                        sheet.write(row, col, "", self.get_format(workbook))
                    col += 1
                    if picking.export_clause:
                        sheet.write(row, col, picking.export_clause.name, self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, line.product_id.get_caning(), self.get_format(workbook))
                    col += 1
                    if picking.charging_mode:
                        sheet.write(row, col, picking.charging_mode, self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, 'Si' if picking.client_label else 'No', self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, line.product_id.get_brand(), self.get_format(workbook))
                    col += 1
                    if picking.agent_id:
                        sheet.write(row, col, picking.agent_id.name, self.get_format(workbook))
                    col += 1
                    if picking.commission:
                        sheet.write(row, col, picking.commission, self.get_format(workbook))
                    col += 1
                    if picking.total_commission:
                        sheet.write(row, col, picking.total_commission, self.get_format(workbook, 'number'))
                    col += 1
                    if picking.departure_port:
                        sheet.write(row, col, picking.departure_port.name, self.get_format(workbook))
                    col += 1
                    if picking.arrival_port:
                        sheet.write(row, col, picking.arrival_port.name, self.get_format(workbook))
                    col += 1
                    if picking.city_final_destiny_id:
                        sheet.write(row, col, picking.city_final_destiny_id.city_country, self.get_format(workbook))
                    col += 1
                    if picking.type_transport:
                        sheet.write(row, col, picking.type_transport.name, self.get_format(workbook))
                    col += 1
                    if picking.plant:
                        sheet.write(row, col, picking.plant.name)
                    col += 1
                    if picking.required_loading_date:
                        sheet.write(row, col, picking.required_loading_date, self.get_format(workbook, 'date'))
                    col += 1
                    if picking.dte_folio:
                        sheet.write(row, col, picking.dte_folio, self.get_format(workbook))
                    col += 1
                    shipping_number = '%s / %s' % (picking.ship.name, picking.ship_number)
                    if not picking.ship and not picking.ship_number:
                        shipping_number = ''
                    sheet.write(row, col, shipping_number)
                    col += 1
                    if picking.shipping_company:
                        sheet.write(row, col, picking.shipping_company.name, self.get_format(workbook))
                    col += 1
                    if picking.booking_number:
                        sheet.write(row, col, picking.booking_number, self.get_format(workbook))
                    col += 1
                    if picking.bl_number:
                        sheet.write(row, col, picking.bl_number, self.get_format(workbook))
                        total_bl += 1
                    col += 1
                    if picking.stacking:
                        sheet.write(row, col, picking.stacking, self.get_format(workbook))
                    col += 1
                    if picking.cut_off:
                        sheet.write(row, col, picking.cut_off, self.get_format(workbook))
                    col += 1
                    if picking.departure_date:
                        sheet.write(row, col, picking.departure_date, self.get_format(workbook, 'date'))
                    col += 1
                    if picking.arrival_date:
                        sheet.write(row, col, picking.arrival_date, self.get_format(workbook, 'date'))
                    col += 1
                    if picking.container_number:
                        sheet.write(row, col, picking.container_number, self.get_format(workbook))
                        total_container += 1
                    col += 1
                    if picking.container_type:
                        sheet.write(row, col, picking.container_type.name, self.get_format(workbook))
                    col += 1
                    if picking.port_terminal_origin:
                        sheet.write(row, col, picking.port_terminal_origin, self.get_format(workbook))
                    col += 1
                    if picking.withdrawal_deposit:
                        sheet.write(row, col, picking.withdrawal_deposit.name, self.get_format(workbook))
                    col += 1
                    if picking.freight_value:
                        sheet.write(row, col, picking.freight_value, self.get_format(workbook, 'number'))
                    col += 1
                    # Valor Seguro
                    sheet.write(row, col, picking.safe_value, self.get_format(workbook, 'number'))
                    col += 1
                    # FOB TOTAL
                    total_fob += picking.total_value if picking.total_value > 0 else 0
                    sheet.write(row, col, picking.total_value if picking.total_value > 0 else 0,
                                self.get_format(workbook, 'number'))
                    col += 1
                    # FOB POR KILO

                    sheet.write(row, col, picking.value_per_kilogram if picking.value_per_kilogram > 0 else 0,
                                self.get_format(workbook, 'number'))
                    col += 1
                    sheet.write(row, col, picking.quality_remarks if picking.quality_remarks else '',
                                self.get_format(workbook))

                    col += 1
                    sheet.write(row, col, picking.remarks if picking.remarks else '', self.get_format(workbook))
                    col += 1
                    sheet.write(row, col, picking.dus_number if picking.dus_number else '', self.get_format(workbook))
                    col += 1
                    col = 0
                    row += 1
                    sheet.write(row, 0, "Total", self.get_format(workbook, 'title_number'))
                    # sheet.write(row, 20, total_kilogram, formats['title_number'])
                    sheet.write_formula(row, 20, '=SUM(U2:U%s)' % (row - 1), self.get_format(workbook, 'title_number'))
                    sheet.write(row, 22, '=SUM(W2:W%s)' % (row - 1), self.get_format(workbook, 'title_number'))
                    sheet.write(row, 31, '=SUM(AF2:AF%s)' % (row - 1), self.get_format(workbook, 'title_number'))
                    sheet.write(row, 42, total_bl, self.get_format(workbook, 'title_number'))
                    sheet.write(row, 47, total_container, self.get_format(workbook, 'title_number'))
                    sheet.write(row, 51, '=SUM(AZ2:AZ%s)' % (row - 1), self.get_format(workbook, 'title_number'))
                    sheet.write(row, 52, '=SUM(BA2:BA%s)' % (row - 1), self.get_format(workbook, 'title_number'))
                    sheet.write(row, 53, '=SUM(BB2:BB%s)' % (row - 1), self.get_format(workbook, 'title_number'))
                    sheet.write(row, 54, '=SUM(BC2:BC%s)' % (row - 1), self.get_format(workbook, 'title_number'))

        sheet.autofit()
        workbook.close()
        with open(file_name, 'rb') as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Archivo de Pedido - {}'.format(self.for_year)
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': file_name,
            'datas_fname': file_name,
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
