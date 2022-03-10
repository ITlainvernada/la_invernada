from odoo import http, exceptions, models
from odoo.http import request
from datetime import date, timedelta
import werkzeug


class DryProcessController(http.Controller):

    @http.route('/api/dry_process', type='json', methods=['GET'], auth='token', cors='*')
    def get_dry_process(self, sinceDate=None):
        search_date = sinceDate or (date.today() - timedelta(days=7))
        result = request.env['dried.unpelled.history'].sudo().search([('write_date', '>', search_date)])
        processResult = []
        for res in result:
            if res.finish_date:
                processResult.append({
                    'name': res.name,
                    'inLotIds': res.mapped('in_lot_ids.name'),
                    'initDate': res.init_date or res.create_date,
                    'guideNumbers': res.lot_guide_numbers,
                    'finishDate': res.finish_date or res.write_date,
                    'productName': res.in_product_id.name,
                    'productId': res.in_product_id.id,
                    'productVariety': res.in_product_variety,
                    'outLot': res.out_lot_id.name,
                    'producerName': res.producer_id.name,
                    'producerId': res.producer_id.id,
                    'totalInWeight': res.total_in_weight,
                    'totalOutWeight': res.total_out_weight,
                    'performance': res.performance,
                    'OdooUpdatedAt': res.write_date
                })
        result_dried = request.env['unpelled.dried'].sudo().search(
            [('write_date', '>', search_date), ('state', '=', 'progress')])
        for res in result_dried:
            processResult.append({
                'name': res.name,
                'inLotIds': [lot.name for lot in res.in_lot_ids],
                'initDate': res.oven_use_ids[0].init_date if len(res.oven_use_ids) > 0 else res.create_date,
                'guideNumber': self.get_guide_number(res),
                'finishDate': res.write_date,
                'productName': res.product_in_id.name,
                'productId': res.product_in_id.id,
                'outLot': res.out_lot_id.name,
                'producerName': res.producer_id.name,
                'totalInWeight': res.total_in_weight,
                'totalOutWeight': res.total_out_weight,
                'performance': res.performance,
                'OdooUpdatedAt': res.write_date
            })
        return processResult

    def get_guide_number(self,res):
        tmp = ''
        for guide_number in res.in_lot_ids.mapped('reception_guide_number'):
            tmp += '{} '.format(guide_number)
        return tmp