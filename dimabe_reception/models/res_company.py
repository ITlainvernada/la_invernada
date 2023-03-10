from odoo import models, fields
import urllib3
import json
import pytz
import requests

class ResCompany(models.Model):
    _inherit = 'res.company'

    sag_code = fields.Char('CSG')

    def get_quality_login_token(self):
        url = 'https://qacalidadapi.lainvernada.com/api/auth/login'
        http = urllib3.PoolManager()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        json_data = {
            'Username': '66.666.666-6',
            'Password': 'Dimabe2023$'
        }
        res = requests.post(url, json=json.dumps(json_data), headers=headers)

        if res.token:
            return res.token
        return False

    def set_lot_to_quality_api(self, model):
        token = self.get_quality_login_token()
        if token:
            url = 'https://qacalidadapi.lainvernada.com/api/LotFromDryers/add'
            http = urllib3.PoolManager()
            headers = {
                'Content-Type': 'application/json',
                'Accept': "application/json",
                'Authorization': 'Bearer {}'.format(token)
            }
            json_data = {
                'ProducerCode': 145,
                'ProducerName': 'Alejandro del Río Artigas',
                'VarietyName': 'Chandler',
                'LotNumber': '801846469',
                'DispatchGuideNumber': '68465',
                'ReceptionDate': '2022-03-09',
                'ReceptionKgs': '8500',
                'ContainerType': 'MAXISACO 2,2 M',
                'ContainerWeightAverage': '655,41',
                'ContainerWeight': '',
                'Season': 2020,
                'Warehouse': 'BODEGA  TERCEROS',
                'ContainerQuantity': '22',
                'ArticleCode': '1000010001',
                'ArticleDescription': 'NUEZ CHANDLER C/CÁSCARA SIN CALIBRAR'
            }
            res = requests.post(url, json=json.dumps(json_data), headers=headers)