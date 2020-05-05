from odoo import models, fields, api
import json
import requests
from datetime import date

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    dte_folio = fields.Text(string='Folio DTE')
    dte_type_id =  fields.Many2one(
        'dte.type', string = 'Tipo Documento'
    )
    dte_xml = fields.Text("XML")
    dte_pdf = fields.Text("PDF")
    ted = fields.Text("TED")
    pdf_url = fields.Text("URL PDF")

    partner_economic_activities = fields.Many2many('custom.economic.activity',related='partner_id.economic_activities')
    company_economic_activities = fields.Many2many('custom.economic.activity', related='company_id.economic_activities')
    partner_activity_id = fields.Many2one('custom.economic.activity', string='Actividad del Proveedor')
    company_activity_id = fields.Many2one('custom.economic.activity', string='Actividad de la Compañía')
    references = fields.One2many(
        'account.invoice.references',
        'invoice_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    method_of_payment = fields.Selection(
        [
            ('1', 'Contado'),
            ('2', 'Crédito'),
            ('3', 'Gratuito')
        ],
        string="Forma de pago",
        readonly=True,
        states={'draft': [('readonly', False)]},
        default='1',
    )

    @api.onchange('partner_id')
    @api.multi
    def _compute_partner_activity(self):
        for item in self:
            activities = []
            for activity in item.partner_id.economic_activities:
                activities.append(activity.id)
            item.partner_activity_id = activities
    @api.one
    def send_to_sii(self):
        #PARA COMPLETAR EL DOCUMENTO SE DEBE BASAR EN http://www.sii.cl/factura_electronica/formato_dte.pdf
        if not self.company_activity_id or not self.partner_activity_id:
            raise models.ValidationError('Por favor seleccione las actividades de la compañía y del proveedor')
        if not self.company_id.invoice_rut or not self.partner_id.invoice_rut:
            raise models.ValidationError('No se encuentra registrado el rut de facturación')

        if not self.dte_type_id:
            raise models.ValidationError('Por favor seleccione tipo de documento a emitir')
        if not self.company_activity_id or not self.partner_activity_id:
            raise models.ValidationError('Debe seleccionar el giro de la compañí y proveedor a utilizar')

        dte = {}
        dte["Encabezado"] = {}
        dte["Encabezado"]["IdDoc"] = {}
        # El Portal completa los datos del Emisor
        dte["Encabezado"]["IdDoc"] = {"TipoDTE": str(self.dte_type_id.code)}
        #Si es Boleta de debe indicar el tipo de servicio, por defecto de venta de servicios
        if self.dte_type_id.code in ('39', 39):
            dte["Encabezado"]["IdDoc"]["IndServicio"] = 3

        if not self.dte_type_id.code in ('39', 39):
            #Se debe inicar SOLO SI los valores indicados en el documento son con iva incluido
            dte["Encabezado"]["IdDoc"]["MntBruto"] = 1

        #EL CAMPO RUT DE FACTURACIÓN, debe corresponder al RUT de la Empresa
        dte["Encabezado"]["Emisor"] = {"RUTEmisor": self.company_id.invoice_rut.replace(".","")}

        # EL CAMPO VAT o NIF Del Partner, debe corresponder al RUT , si es empresa extranjera debe ser 55555555-5
        dte["Encabezado"]["Receptor"] = {"RUTRecep": self.partner_id.invoice_rut.replace(".",""),
                                         "RznSocRecep": self.partner_id.name,
                                         "DirRecep": self.partner_id.street +  ' ' + self.partner_id.city,
                                         "CmnaRecep": self.partner_id.city,
                                         "GiroRecep": self.partner_activity_id.name}
        
        dte["Encabezado"]["IdDoc"]["TermPagoGlosa"] = self.comment or ''
        dte["Encabezado"]["IdDoc"]["Folio"] = '0'
        dte["Encabezado"]["IdDoc"]["FchEmis"] = str(date.today())
        dte["Detalle"] = []
        for line in self.invoice_line_ids:
            #El Portal Calculos los Subtotales
            ld = {'NmbItem': line.product_id.name,
             'DscItem': '',
             'QtyItem': round(line.quantity, 6),
             'PrcItem': round(line.price_unit,4)
            }
            if line.product_id.default_code:
                ld['CdgItem'] = {"TpoCodigo": "INT1",
                              "VlrCodigo": line.product_id.default_code}
            if line.discount:
                ld['DescuentoPct']= round(line.discount,2)
            dte["Detalle"].append(ld)
        referencias = []
        for reference in self.references:
            ref = {'TpoDocRef':reference.document_type_reference or 'SET',
                   'FolioRef':reference.folio_reference,
                   'FchRef':reference.document_date.__str__(),
                   'RazonRef':reference.reason}
            if reference.code_reference:
                ref['CodRef'] =reference.code_reference
            referencias.append(ref)
        if referencias:
            dte['Referencia'] = referencias
        raise models.ValidationError(json.dumps(dte))
        self.send_dte(json.dumps(dte))

    def send_dte(self, dte):
        url = self.company_id.dte_url
        rut_emisor = self.company_id.invoice_rut.replace(".", "").split("-")[0]
        hash = self.company_id.dte_hash
        auth = requests.auth.HTTPBasicAuth(hash, 'X')
        ssl_check = False
        # Api para Generar DTE
        apidte = '/dte/documentos/gendte?getXML=true&getPDF=true&getTED=png'
        emitir = requests.post(url + '/api' + apidte, dte, auth=auth, verify=ssl_check)
        if emitir.status_code != 200:
            raise Exception('Error al Temporal: ' + emitir.json())
        data = emitir.json()
        self.dte_folio = data.get('folio', None)
        self.dte_xml = data.get("xml", None)
        self.ted = data.get("ted", None)
        fecha = data.get("fecha", None)
        total = data.get("total", None)
        self.pdf_url = "%s/dte/dte_emitidos/pdf/%s/%s/0/%s/%s/%s" % (url, self.tipo_dte, self.folio_dte, rut_emisor, fecha, total)
