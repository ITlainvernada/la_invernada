# -*- coding: utf-8 -*-
{
    'name': "Proceso de Compras",

    'summary': """
        proceso de recepción para la invernada""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Dimabe ltda",
    'website': "http://www.dimabe.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Solicitud de Compra',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'purchase_requisition',
        'purchase',
        'dimabe_billing_rut'
    ],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/purchase_order.xml',
        'views/purchase_requisition.xml',
        'views/res_company.xml',
        'data/purchase_requisition_mail_template.xml',
        'data/purchase_order_mail_template.xml',
        'reports/purchase_order_reports.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
