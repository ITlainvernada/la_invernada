{
    'name': 'Notas de Credito POS',
    'version': '1.0.0.0',
    'category': 'Point of Sale',
    'summary': """Devoluciones desde el POS mediante Notas de credito""",
    'sequence': 5,
    'author': 'Flectra Chile SPA',
    'website': 'http://flectrachile.cl/',
    'excludes': [
        'l10n_cl_pos_return',
    ],
    'depends': [
        'base',
        'mail',
        'web',
        'point_of_sale',
        'pos_base',
        'generic_pos',
        'pos_orders_history_return',
        'l10n_cl_fe',
        'l10n_cl_dte_point_of_sale',
        'pos_stock_quantity',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_credit_note_pos_view.xml',
        'views/pos_order_reason_nc_view.xml',
        'views/pos_order_view.xml',
        'views/l10n_cl_pos_order_history_return_assets.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}