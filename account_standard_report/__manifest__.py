# -*- coding: utf-8 -*-

{
    'name': 'Contabilidad: Reportes Standard',
    'version': '12.0.1.0.1',
    'category': 'Accounting',
    'author': 'Mobilize SPA',
    'summary': 'Contabilidad: Reportes Standard',
    'website': 'https://mobilize.cl',
    'depends': ['account', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'data/report_paperformat.xml',
        'data/data_account_standard_report.xml',
        'data/res_currency_data.xml',
        'report/report_account_standard_report.xml',
        'views/account_view.xml',
        'views/account_standard.xml',
        'views/account_standard_report_template_view.xml',
        'views/res_currency_views.xml',
        'wizard/account_standard_report_view.xml',
    ],
    'demo': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    "images":['static/description/icon.png'],
}
