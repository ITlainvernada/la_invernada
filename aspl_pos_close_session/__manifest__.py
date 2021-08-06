# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': 'POS Close Session',
    'category': 'Point of Sale',
    'summary': 'Close session from POS,It manage cash control while closing the session,'
               'It also print Z report(end of the session report) and '
                'send close session report via email to selected users.',
    'description': """
    Close session from POS,It manage cash control while closing the session,
    It also print Z report(end of the session report).
       """,
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'price': 35.00,
    'currency': 'EUR',
    'version': '1.0.1',
    'depends': [
        'base', 
        'point_of_sale',
        'odoo_utils',
        'generic_pos',
        'payment_cash_register',
        'account_credit_card_base',
    ],
    'images': ['static/description/main_screenshot.png'],
    "data": [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/data.xml',
        'views/pos_z_report_template.xml',
        'views/pos_z_thermal_report.xml',
        'views/report.xml',
        'reports/report_pos_deposit.xml',
        'wizard/wizard_session_resume_view.xml',
        'wizard/wizard_pos_deposit_view.xml',
        'views/account_bank_statement_view.xml',
        'views/pos_register.xml',
        'views/pos_config_view.xml',
        'views/pos_session_view.xml',
        'views/res_users_view.xml',
        'views/pos_session_resume.xml',
        'views/pos_deposit_view.xml',
        'views/pos_cashbox_view.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: