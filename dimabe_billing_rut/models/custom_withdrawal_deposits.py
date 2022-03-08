from odoo import models, fields, api

class CustomWithdrawalDeposits(models.Model):

    _name = 'custom.withdrawal.deposits'
    _description = "Retiro de Depositos"

    name = fields.Char(string= 'Nombre', required=True)
