# -*- coding: utf-8 -*-

from odoo import fields, models
import logging
_logger = logging.getLogger('TEST PURCHASE =======')


class AccountBalanceReport(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = 'account.balance.report'
    _description = 'Trial Balance Report'

    journal_ids = fields.Many2many('account.journal', 'account_balance_report_journal_rel', 'account_id', 'journal_id', string='Journals', required=True, default=[])

    def _print_report(self, data):
        data = self.pre_print_report(data)
        records = self.env[data['model']].browse(data.get('ids', []))
        _logger.info('LOG: ----> data {}'.format(data))
        return self.env.ref('l10n_cl_balance.action_report_trial_balance').report_action(records, data=data)
