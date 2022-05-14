# coding=utf-8
import io

from odoo import fields, api, models, _, tools
from datetime import datetime
import pytz
import calendar
import re

from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, format_date

from pprint import pprint
from io import BytesIO

import logging
import base64
import json
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, Warning, CacheMiss
from odoo.tools.misc import formatLang

import xlsxwriter
import logging

_logger = logging.getLogger(__name__)

YEAR_REGEX = re.compile("^[0-9]{4}$")
DATE_FORMAT = '%Y-%m-%d'
fmt = '%Y-%m-%d %H:%M:%S'

MONTH_SELECTION = [('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'), ('4', 'Abril'), ('5', 'Mayo'),
                   ('6', 'Junio'), ('7', 'Julio'), ('8', 'Agosto'), ('9', 'Setiembre'), ('10', 'Octubre'),
                   ('11', 'Noviembre'), ('12', 'Diciembre')]


class ExcelWizard(models.TransientModel):
    _name = "backup.xlsx.report.wizard"
    # start_date = fields.Datetime(string="Start Date", default=time.strftime('%Y-%m-01'), required=True)
    # end_date = fields.Datetime(string="End Date", default=datetime.datetime.now(), required=True)

    # option = fields.Selection(
    #     string='Opciones',
    #     selection=[('all', 'All'),
    #                ('company', 'Company'), ], default='all',
    #     required=True)

    type_report = fields.Selection(
        string='Tipo de reporte',
        selection=[('base', 'Base'),
                   ('detail', 'Detalle'), ], default='detail',
        required=True)

    def _default_month(self):
        user_tz = self.env.user.tz or 'America/Bogota'
        timezone = pytz.timezone(user_tz)
        current = datetime.now(timezone)
        return str(current.month)

    def _default_year(self):
        user_tz = self.env.user.tz or 'America/Bogota'
        timezone = pytz.timezone(user_tz)
        current = datetime.now(timezone)
        return str(current.year)

    range = fields.Selection([
        ('month', 'Por mes'),
        ('dates', 'Fechas'),
        ('date', 'Por día'),
        ('all', 'Todos'),
    ], 'Fecha', default='month', required=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company',
        required=False,
        ondelete='cascade',
    )
    month = fields.Selection(MONTH_SELECTION, string='Mes', default=_default_month)
    year = fields.Char('Año', default=_default_year)
    date_start = fields.Date('Desde')
    date_end = fields.Date('Hasta')

    def _get_current_date(self):
        """ :return current date """
        return datetime.now(pytz.timezone(self.env.user.tz or 'America/Bogota')).date()

    date_def = fields.Date('Día', default=lambda self: self._get_current_date())
    hour_def = fields.Float('Hora')

    hour_start = fields.Float('Hora inicio')
    hour_end = fields.Float('Hora fin')

    @api.onchange('year')
    def onchange_year(self):
        if self.year is False or not bool(YEAR_REGEX.match(self.year)):
            raise ValidationError('Debe especificar un año correcto')

    @api.constrains('date_start', 'date_end')
    def check_dates(self):
        if self.date_start is not False and \
                self.date_end is not False:
            if self.date_end < self.date_start:
                raise ValidationError('La fecha de inicio debe ser menor o igual que la fecha de fin')

    @api.onchange('range', 'month')
    def onchange_range(self):
        if self.range == 'month':
            w, days = calendar.monthrange(int(self.year), int(self.month))
            self.date_start = datetime.strptime('{}-{}-{}'.format(self.year, self.month, 1), DATE_FORMAT).date()
            self.date_end = datetime.strptime('{}-{}-{}'.format(self.year, self.month, days), DATE_FORMAT).date()
        # print(self.date_start, self.date_end)

    # ----------------------------------------
    @api.constrains('date_start', 'date_end')
    def check_parameters(self):
        for record in self:
            if record.date_start and record.date_end:
                start = record.date_start.strftime(DEFAULT_SERVER_DATE_FORMAT)
                end = record.date_end.strftime(DEFAULT_SERVER_DATE_FORMAT)
                if start > end:
                    raise ValidationError('La fecha de fin debe ser mayor que la de inicio')

    # ----------------------------------------

    def _get_name_rpt(self):
        if self.range == 'month':
            month_label = dict(self.fields_get("month", "selection")["month"]["selection"])
            return f'({month_label[self.month]}/{self.year}) para {self.company_id.name}'
        elif self.range == 'dates':
            return f'({self.date_start} AL {self.date_end})  para {self.company_id.name}'
        elif self.range == 'date':
            return f'({self.date_start})  para {self.company_id.name}'
        else:
            return f'(Todos) para {self.company_id.name}'

    # def get_domain(self):
    #     domain = [('company_id', '=', self.company_id.id)]
    #     return domain

    def print_xlsx(self):
        # if self.start_date > self.end_date:
        #     raise ValidationError('Start Date must be less than End Date')
        data = []

        HRP = self.env['hr.payslip'].sudo()
        HRPL = self.env['hr.payslip.line'].sudo()
        domain = [('company_id', '=', self.company_id.id)]

        # if self.option == 'company':
        #     domain += [('company_id', '=', self.company_id.id)]

        # print(payslips[0].read())

        def get_amount_code(p, code_def):
            return p.line_ids.filtered(lambda line: line.appears_on_payslip and line.code == code_def).total or 0.0

        def get_amount_he_code(hpl, code_def):
            return hpl.slip_id.input_line_ids.filtered(lambda line: line.code == code_def).amount or False

        if self.type_report == 'detail':
            # lines = []
            if self.range == 'dates':
                sql = """
                    SELECT * FROM hr_payslip_line as hpl 
                    WHERE DATE(hpl.create_date) BETWEEN '{0}' AND '{1}'
                """.format(self.date_start, self.date_end)
                _logger.info('SQL: {}'.format(sql))

                self.env.cr.execute(sql)
                query_res = self.env.cr.dictfetchall()
                ids = [record['id'] for record in query_res]
                lines = HRPL.browse(ids)
            elif self.range == 'month':
                data = HRPL.search(domain)
                lines = data.filtered(
                    lambda o: o.create_date.month == int(self.month) and o.create_date.year == int(self.year))
            elif self.range == 'date':
                data = HRPL.search(domain)
                lines = data.filtered(
                    lambda o: o.create_date.day == int(self.date_def.day) and o.create_date.month == int(
                        self.date_def.month) and o.create_date.year == int(self.date_def.year))
            else:
                lines = HRPL.search(domain)

            for hpl in lines:
                HEX50 = 0
                wage = 0
                if hpl.code == 'HEX50':
                    HEX50 = get_amount_he_code(hpl, 'HEX50')

                    wage = hpl.contract_id.wage

                item = {
                    'name': hpl.name,
                    'code': hpl.code,
                    'HEX50': HEX50,
                    'wage': wage,
                    'amount': hpl.amount,
                    'name_employee': hpl.employee_id.name,
                    'rut': hpl.employee_id.identification_id,
                    'appears_on_payslip': 'SI' if hpl.appears_on_payslip else 'NO',
                    'date_from': hpl.slip_id.date_from,
                    'date_to': hpl.slip_id.date_to,
                    'company': hpl.company_id.name,
                }
                data.append(item)

        else:
            # payslips = HRP.search(domain)

            if self.range == 'dates':
                domain += [('create_date', '>=', self.date_start), ('create_date', '<=', self.date_end)]
                payslips = HRP.search(domain)
            elif self.range == 'month':
                data = HRP.search(domain)
                payslips = data.filtered(
                    lambda o: o.create_date.month == int(self.month) and o.create_date.year == int(self.year))
            elif self.range == 'date':
                data = HRP.search(domain)
                payslips = data.filtered(
                    lambda o: o.create_date.day == int(self.date_def.day) and o.create_date.month == int(
                        self.date_def.month) and o.create_date.year == int(self.date_def.year))
            else:
                payslips = HRP.search(domain)

            for payslip in payslips:
                # if self.type_report == 'detail':
                #
                #     # HEX50 = get_amount_he_code(payslip, 'HEX50')
                #     # if HEX50:
                #     #     item = {
                #     #         'rut': payslip.employee_id.identification_id,
                #     #         'HEX50': HEX50.amount,
                #     #         'base_amount': payslip.contract_id.wage
                #     #     }
                #     #     data.append(item)
                # else:
                TOTIM = get_amount_code(payslip, 'TOTIM')
                date_to = payslip.date_to.strftime('%d-%m-%Y') if payslip.date_to else ''
                item = {
                    'A': "",
                    'B': payslip.employee_id.identification_id,
                    'C': date_to,
                    'D': get_amount_code(payslip, 'SUELDO'),
                    'E': TOTIM,
                    'F': payslip.worked_days_line_ids.filtered(lambda wd: wd.code == 'WORK100').number_of_days,
                    'G': TOTIM,
                    'H': "",
                    'I': get_amount_code(payslip, 'PREV'),
                    'J': get_amount_code(payslip, 'SALUD'),
                    'K': get_amount_code(payslip, 'TRIBU'),
                    'L': get_amount_code(payslip, 'IMPUNI'),
                    'M': "",
                    'N': get_amount_code(payslip, 'SECE'),
                    'O': "",
                    'P': get_amount_code(payslip, 'SECEEMP'),
                    'Q': "",
                    'R': "",
                    'S': "",
                    'T': "",
                    'U': "",
                    'V': get_amount_code(payslip, 'LIQ'),
                    'W': "",
                    'X': "",
                    'Y': "",
                    'AA': "",
                    'AB': "",
                    'AC': "",
                    'AD': "",
                    'AE': "",
                    'AF': "",
                    'AG': "",
                    'AH': "",
                    'AI': "",
                    'AJ': "",
                    'AK': "",
                    'AL': "",
                    'AN': "",
                    'AO': "",
                    'AP': "",
                    'AQ': "",
                    'AR': "",
                    'AS': "",
                    'AT': "",
                    'AU': "",
                    'AV': "",
                    'AW': "",
                    'AX': "",
                    'AY': "",
                }
                data.append(item)

        data_dic = {
            'lines': data,
            'type_report': self.type_report
        }
        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'backup.xlsx.report.wizard',
                     'options': json.dumps(data_dic, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': self._get_name_rpt(),
                     }
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format({'align': 'left', 'bold': True, 'font_size': '10px'})
        txt = workbook.add_format({'font_size': '10px'})

        if data['type_report'] == 'detail':
            titles = ['NOMBRE', 'CODIGO', 'HEX50', 'BASE AMOUNT', 'IMPORTE', 'NOMBRE_EMPLEADO',
                      'NRO_IDENTIFICACION', 'APARECE_EN_NOMINA', 'FECHA_DESDE', 'FECHA_HASTA', 'COMPAÑÍA']
            sheet.write_row(0, 0, titles, head)
            sheet.set_column(0, 12, 20)
        else:
            titles = [
                'Company Code', 'Employee Code', 'Payment Date', 'Base Salary', 'Total Taxable(Uncapped)',
                'Worked Days',
                'Total Taxable(Capped)', 'AFP % quote', 'Total AFP quote', 'Total Health quote', 'Tax Base', 'Tax',
                'Voluntary PPM', 'Quote Employee Unemployment Insurance',
                "Total Capped Taxable AFC regarding Employee's Unemployment Insurance",
                'Quote Company Unemployement Insurance Solidarity Fund',
                'Quote Company Unemployment Insurance Individual Fund',
                "Total Capped Taxable AFC regarding Employer's Unemployment Insurance", 'Other Discounts Total',
                'Free Total Assets', 'APV (Only Regime B)', 'Net Paid', '% Employee Heavy Duty Quote',
                'Heavy Duty QuoteEmployee', "Employer's Heavy Duty Contribution", 'Total Taxable CAPPED for Heavy Duty',
                "% Employer's Mutual Quote", "Employer's Mutual contribution",
                "TOP Taxable Amount for Mutual", "% Employer's SIS Quote", 'SIS Employer Contribution',
                'TOP Taxable Amount for SIS', 'Total Extreme Zone Rebate', 'License Days (Medical Leave)',
                'Vacations Days', 'Other Leave days', 'Absence days',
                'Amount taxable for Medical Leave Subsidy',
                'Medical Leave Net Subsidy', 'Gross amount subject to Resettlement',
                'Resettlement AFP ', 'Resettlement HEALTH', 'Unemployement Insurance (employee) Resettlement',
                'Resettlement Tax', 'Heavy Duty (Employee) Resettlement', 'Heavy Duty Contribution Resettlement',
                'Mutual Contribution Resettlement', 'SIS Contribution Resettlement',
                'Unemployemnt Insurance Contribution (Individual Fund) Resettlement',
                'Unemployemnt Insurance Contribution Solidarity Fund) Resettlement', 'Resettlement Period'
            ]
            sheet.write_row(0, 0, titles, head)
            sheet.set_column(0, 50, 20)

        for idx, item in enumerate(data['lines']):
            new_list = list(item.values())
            sheet.write_row(idx + 1, 0, new_list, txt)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
