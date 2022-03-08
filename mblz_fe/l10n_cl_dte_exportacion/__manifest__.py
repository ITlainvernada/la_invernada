# -*- coding: utf-8 -*-
{
    "name": """Factura de Exportación Electrónica para Chile\
    """,
    'version': '0.19.0',
    'category': 'Localization/Chile',
    'sequence': 12,
    'author':  'Daniel Santibáñez Polanco, Cooperativa OdooCoop',
    'website': 'https://globalresponse.cl',
    'license': 'AGPL-3',
    'summary': '',
    'description': """
Chile: Factura de Exportación Electrónica.
""",
    'depends': [
            'base',
            'product',
            'uom',
            'stock',
            'delivery',
            'l10n_cl_fe',
    ],
    'data': [
            'views/aduanas_formas_pago.xml',
            'views/aduanas_modalidades_venta.xml',
            'views/aduanas_paises.xml',
            'views/aduanas_puertos.xml',
            'views/aduanas_tipos_bulto.xml',
            'views/aduanas_tipos_carga.xml',
            'views/aduanas_tipos_transporte.xml',
            'views/invoice_exportacion.xml',
            'views/invoice_view.xml',
            'views/payment_terms.xml',
            'views/uom_uom.xml',
            'views/account_incoterms.xml',
            'views/layout.xml',
            # 'security/ir.model.access.csv',
            # 'data/aduanas.formas_pago.csv',
            # 'data/aduanas.modalidades_venta.csv',
            'data/aduanas_paises.xml',
            # 'data/res.country.csv',
            # 'data/aduanas.puertos.csv',
            # 'data/aduanas.tipos_bulto.csv',
            # 'data/aduanas.tipos_carga.csv',
            # 'data/aduanas.tipos_transporte.csv',
            'data/uom_uom.xml',
            'data/account.incoterms.csv',
    ],
    'installable': True,
    'application': True,
}
