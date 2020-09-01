# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import fields, models, _


class UpdatWBReports(models.TransientModel):
    _name = "updat.wb.reports"
    _description = "Updating wildberries reports"

    date_from = fields.Date('Date from', required=True)
    date_to = fields.Date('Date to')
    
    def updat_wb_incomes(self):
        conn_wb = self.env['connector.wb'].with_context(date_from=str(self.date_from))
        conn_wb.synchronize_events(reportType='incomes')

        return self.action_view_wb_report(reportType='incomes')

    def updat_wb_stocks(self):
        conn_wb = self.env['connector.wb'].with_context(date_from=str(self.date_from))
        conn_wb.synchronize_events(reportType='stocks')

        return self.action_view_wb_report(reportType='stocks')

    def updat_wb_orders(self):
        conn_wb = self.env['connector.wb'].with_context(date_from=str(self.date_from), 
            db_cleanup_suffix='hours')
        conn_wb.synchronize_events(reportType='orders', flag = 0)

        return self.action_view_wb_report(reportType='orders')

    def updat_wb_sales(self):
        conn_wb = self.env['connector.wb'].with_context(date_from=str(self.date_from), 
            db_cleanup_suffix='hours')
        conn_wb.synchronize_events(reportType='sales', flag = 0)

        return self.action_view_wb_report(reportType='sales')

    def updat_wb_report_detail_by_period(self):
        conn_wb = self.env['connector.wb'].with_context(date_from=str(self.date_from), 
            date_to=str(self.date_to), db_cleanup_suffix='hours')
        conn_wb.synchronize_events(reportType='reportDetailByPeriod', flag = 0)

        return self.action_view_wb_report(reportType='reportDetailByPeriod')

    def updat_wb_sales_1(self):
        conn_wb = self.env['connector.wb']
        conn_wb.synchronize_events_cron('sales', 1, 'months')

        return self.action_view_wb_report(reportType='sales')

    def updat_wb_report_detail_by_period_cron(self):
        conn_wb = self.env['connector.wb']
        conn_wb.synchronize_events_cron('reportDetailByPeriod', 2, 'months')

        return self.action_view_wb_report(reportType='reportDetailByPeriod')

    def action_view_wb_report(self, reportType):
        if reportType == 'incomes':
            action = self.env.ref('connector_wb.wb_incomes_action').read()[0]
        elif reportType == 'stocks':
            action = self.env.ref('connector_wb.wb_stocks_action').read()[0]
        elif reportType == 'orders':
            action = self.env.ref('connector_wb.wb_orders_action').read()[0]
        elif reportType == 'sales':
            action = self.env.ref('connector_wb.wb_sales_action').read()[0]
        elif reportType == 'reportDetailByPeriod':
            action = self.env.ref('connector_wb.wb_report_detail_by_period_action').read()[0]
        
        return action

