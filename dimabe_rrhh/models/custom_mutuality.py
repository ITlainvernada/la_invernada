from odoo import models, fields, api


class CustomMutuality(models.Model):
    _name = 'custom.mutuality'

    company_id = fields.Many2one('res.partner', 'Compañia',compute='compute_partner_company')

    value = fields.Float('Valor')

    indicator_id = fields.Many2one(comodel_name='hr.indicadores', auto_join=True, string='Indicadores')


    @api.model
    def compute_partner_company(self):
        hr_employee = self.env['hr.employee'].sudo().search([])
        company_ids = hr_employee.mapped('address_id').mapped('id')
        return self.env['res.partner'].sudo().search([('id','in',company_ids)])
