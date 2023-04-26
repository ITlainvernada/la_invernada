from odoo import models, fields
import json
import requests

class ResCompany(models.Model):
    _inherit = 'res.company'

    sag_code = fields.Char('CSG')
