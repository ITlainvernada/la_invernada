from odoo import models, fields
import json
import requests

class ResCompany(models.Model):
    _inherit = 'res.company'

    sag_code = fields.Char('CSG')

    def get_quality_login_token(self):
        url = 'https://qacalidadapi.lainvernada.com/api/auth/login'
        headers = {
            "Content-Type": "application/json",
        }
        json_data = {
            "Username": "66.666.666-6",
            "Password": "Dimabe2023$",
        }
        res = requests.post(url, json=json_data, headers=headers)
        if res.status_code == 200:
            jr = json.loads(res.text)
            token = jr['token']
            return token
        return False

    def set_lot_to_quality_api(self):
        token = self.get_quality_login_token()
        if token:
            bearer = 'Bearer {}'.format(token)
            url = 'https://qacalidadapi.lainvernada.com/api/LotFromDryers/add'
            headers = {
                "Content-Type": "application/json",
                "Authorization": bearer
            }
            json_data = {
                "ProducerCode": 145,
                "ProducerName": "Alejandro del Río Artigas",
                "VarietyName": "Chandler",
                "LotNumber": "801846469",
                "DispatchGuideNumber": "68465",
                "ReceptionDate": "2022-03-09",
                "ReceptionKgs": "8500",
                "ContainerType": "MAXISACO 2,2 M",
                "ContainerWeightAverage": "655,41",
                "ContainerWeight": "",
                "Season": 2020,
                "Warehouse": "BODEGA  TERCEROS",
                "ContainerQuantity": "22",
                "ArticleCode": "1000010001",
                "ArticleDescription": "NUEZ CHANDLER C/CÁSCARA SIN CALIBRAR"
            }
            res = requests.post(url, json=json_data, headers=headers)