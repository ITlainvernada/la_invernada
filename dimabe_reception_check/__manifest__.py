# -*- coding: utf-8 -*-
{
    'name': "Revisión de Recepción",

    'summary': """
        check list para recepciones de productos y hes para servicios
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Dimabe ltda",
    'website': "http://www.dimabe.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'purchase',
        'mail'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking.xml',
        'views/check_list_item.xml',
        'views/check_list_response.xml',
        'views/purchase_order.xml',
        'data/send_hes_mail_template.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}