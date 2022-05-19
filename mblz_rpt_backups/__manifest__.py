# -*- coding: utf-8 -*-
{
    'name': "mblz_rpt_backups",

    'summary': """
        Descarga de reporte de nomina
        """,

    'description': """
       Descarga de reporte de nomina
    """,

    'author': "MOBILIZE",
    'website': "https://www.mobilize.cl",


    'category': 'MOBILIZE/APPS',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['l10n_cl_hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/wizard_view.xml',
        'views/action_manager.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}