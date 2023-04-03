from odoo import exceptions, models
from odoo.http import request
import jwt
from ..jwt_token import decode_token


class ItHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_token(cls):
        token = request.httprequest.headers.get('authorization', '', type=str)
        if token:
            token = token.split(' ')[1]
            try:
                payload = decode_token(token)
                if 'sub' in payload:
                    u = request.env['res.users'].sudo().search(
                        [('id', '=', int(payload['sub']))]
                    )
                    request.uid = u.id
            except jwt.ExpiredSignatureError:
                raise exceptions.AccessDenied()
        else:
            raise exceptions.AccessDenied()
