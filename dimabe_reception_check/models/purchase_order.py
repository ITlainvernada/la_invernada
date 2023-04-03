from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(hes_number)', 'el número ya se encuentra en el sistema')
    ]

    hes_number = fields.Integer(
        'Hoja de entrega de servicio',
        nullable=True,
        default=None,
        readonly=True
    )

    hes_sent_count = fields.Integer(
        'Veces Enviado',
        default=0,
        readonly=True
    )

    has_service = fields.Boolean(
        'Tiene Servicio',
        compute='_has_service_line',
        default=False
    )

    @api.model
    def _has_service_line(self):
        self.has_service = False
        for line in self.order_line:
            if line.product_id.type == 'service':
                self.has_service = True

    @api.multi
    def send_hes(self):
        template_id = self.env.ref('dimabe_reception_check.hes_mail_template')
        self.message_post_with_template(template_id.id)
        self.sum_send_hes()

    @api.returns('self')
    def generate_hes(self):
        self.ensure_one()

        if self.hes_number is None or self.hes_number == 0:
            self._cr.execute('SELECT MAX(hes_number) FROM purchase_order;')
            data = self._cr.fetchall()
            if len(data) == 1 and len(data[0]) == 1 and type(data[0][0]) is int:
                self.hes_number = data[0][0] + 1
            else:
                self.hes_number = 1
        return self

    @api.returns('self')
    def sum_send_hes(self):
        self.ensure_one()
        self.hes_sent_count = self.hes_sent_count + 1
        return self

    @api.multi
    def action_view_invoice(self):

        for order in self:
            if order.has_service:
                if order.hes_number == 0:
                    raise ValidationError('debe validar que recibió el servicio')
                if order.hes_sent_count == 0:
                    raise ValidationError('no ha enviado el número hes al proveedor')

        return super(PurchaseOrder, self).action_view_invoice()
