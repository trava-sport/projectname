# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class UpdatWBReports(models.TransientModel):
    _name = "updat.wb.reports"
    _description = "Updating wildberries reports"

    date = fields.Date('Date from')
    
    def updat_wb_incomes(self):
        conn_wb = self.env['connector.wb'].with_context(date=str(self.date))
        conn_wb.synchronize_events(reportType='incomes')

        return self.action_view_wb_report(reportType='incomes')

    def updat_wb_stocks(self):
        conn_wb = self.env['connector.wb'].with_context(date=str(self.date))
        conn_wb.synchronize_events(reportType='stocks')

        return self.action_view_wb_report(reportType='stocks')

    def action_view_wb_report(self, reportType='None'):
        if reportType == 'incomes':
            action = self.env.ref('connector_wb.wb_incomes_action').read()[0]
        elif reportType == 'stocks':
            action = self.env.ref('connector_wb.wb_stocks_action').read()[0]
        
        return action

