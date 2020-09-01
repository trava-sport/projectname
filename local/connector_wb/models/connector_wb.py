# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

import requests
from dateutil import parser
import json
import logging

from odoo import api, fields, models, tools, _
from odoo.tools import exception_to_unicode
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ConnectorWB(models.AbstractModel):
    STR_SERVICE = 'wb'
    _name = 'connector.%s' % STR_SERVICE
    _description = 'Wildberries connector'

    def get_event_synchro_dict(self, reportType, flag, rrd_id):
        """ Returns events on the 'primary' calendar from google cal.
            :returns dict where the key is the google_cal event id, and the value the details of the event,
                    defined at https://developers.google.com/google-apps/calendar/v3/reference/events/list
        """
        token = self.env['wb.service'].get_client_id('wildberries')

        params = {
            'key': token,
        }

        if reportType == 'incomes' or reportType == 'stocks':
            params['dateFrom'] = self.env.context.get('date_from')
        if reportType == 'orders' or reportType == 'sales':
            params['dateFrom'] = self.env.context.get('date_from')
            params['flag'] = flag
        if reportType == 'reportDetailByPeriod':
            params['dateFrom'] = self.env.context.get('date_from')
            params['limit'] = 100000
            params['rrdid'] = rrd_id
            params['dateTo'] = self.env.context.get('date_to')
        """ params['34'] = self.get_minTime().strftime(
                "%Y-%m-%dT%H:%M:%S.%fz") """

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        url = "/api/v1/supplier/%s" % reportType

        status, content, ask_time = self.env['wb.service']._do_request(
            url, params, headers, reportType, type='GET')

        return content

    # clearing the database before updating
    def deleting_data_in_wb_report(self,reportType,  name_database):
        cr = self._cr
        if reportType == 'incomes' or reportType == 'stocks':
            query = "DELETE FROM %s" % name_database

        if reportType in ('orders', 'sales', 'reportDetailByPeriod'):
            if self.env.context.get('db_cleanup_suffix') == 'hours':
                today = datetime.today().date()
                date_from = self.env.context.get('date_from')
                query = "DELETE FROM %s WHERE last_change_date='%s' OR last_change_date='%s'" % (name_database, today, date_from)
            elif self.env.context.get('db_cleanup_suffix') == 'months':
                if reportType == 'reportDetailByPeriod':
                    date_from = self.env.context.get('date_from')
                    date_to = self.env.context.get('date_to')
                    query = "DELETE FROM %s WHERE '%s'>=rr_dt AND rr_dt>='%s'" % (name_database, date_to, date_from)
                else:
                    date_from = self.env.context.get('date_from')
                    query = "DELETE FROM %s WHERE last_change_date>='%s'" % (name_database, date_from)
        
        cr.execute(query)
        return True

    # def updat_date(self, reportType):
    #     update_date = datetime.strptime(self.env.context.get('date_from'), "%Y-%m-%d")
    #     update_date += timedelta(1)
    #     if update_date == datetime.today().date():
    #         return True
    #     self.with_context(date_from=str(update_date), no_delet=True).update_events(reportType, flag=1)
    #     return True

    def create_from_wildberries_incomes(self, wb):
        for wb_incomes in wb:
            date = {
                'incomeid': wb_incomes['incomeId'],
                'number': wb_incomes['number'],
                'date': datetime.strptime(wb_incomes['date'], "%Y-%m-%dT%H:%M:%S"),
                'last_change_date': datetime.strptime(wb_incomes['lastChangeDate'], "%Y-%m-%dT%H:%M:%S.%f"),
                'supplier_article': wb_incomes['supplierArticle'],
                'barcode': wb_incomes['barcode'],
                'quantity': wb_incomes['quantity'],
                'total_price': wb_incomes['totalPrice'],
                'date_close': datetime.strptime(wb_incomes['dateClose'], "%Y-%m-%dT%H:%M:%S"),
                'warehouse_name': wb_incomes['warehouseName'],
                'nmid': wb_incomes['nmId'],
                'status': wb_incomes['status'],
            }
            self.env['wb.incomes'].create(date)
        return True

    def create_from_wildberries_stocks(self, wb):
        for wb_stocks in wb:
            date = {
                'last_change_date': datetime.strptime(wb_stocks['lastChangeDate'], "%Y-%m-%dT%H:%M:%S.%f"),
                'supplier_article': wb_stocks['supplierArticle'],
                'tech_size': wb_stocks['techSize'],
                'barcode': wb_stocks['barcode'],
                'quantity': wb_stocks['quantity'],
                'is_supply': wb_stocks['isSupply'],
                'is_realization': wb_stocks['isRealization'],
                'quantity_full': wb_stocks['quantityFull'],
                'quantity_not_in_orders': wb_stocks['quantityNotInOrders'],
                'warehouse_name': wb_stocks['warehouseName'],
                'in_way_to_client': wb_stocks['inWayToClient'],
                'in_way_from_client': wb_stocks['inWayFromClient'],
                'nmid': wb_stocks['nmId'],
                'subject': wb_stocks['subject'],
                'category': wb_stocks['category'],
                'days_on_site': wb_stocks['daysOnSite'],
                'brand': wb_stocks['brand'],
                'sccode': wb_stocks['SCCode'],
                'price': wb_stocks['Price'],
                'discount': wb_stocks['Discount'],
            }
            self.env['wb.stocks'].create(date)
        return True

    def create_from_wildberries_orders(self, wb):
        for wb_orders in wb:
            date = {
                'number': wb_orders['number'],
                'date': datetime.strptime(wb_orders['date'], "%Y-%m-%dT%H:%M:%S"),
                'last_change_date': wb_orders['lastChangeDate'],
                'last_change_date_and_time': datetime.strptime(wb_orders['lastChangeDate'], "%Y-%m-%dT%H:%M:%S"),
                'supplier_article': wb_orders['supplierArticle'],
                'tech_size': wb_orders['techSize'],
                'barcode': wb_orders['barcode'],
                'quantity': wb_orders['quantity'],
                'total_price': wb_orders['totalPrice'],
                'discount_percent': wb_orders['discountPercent'],
                'warehouse_name': wb_orders['warehouseName'],
                'oblast': wb_orders['oblast'],
                'income_id': wb_orders['incomeID'],
                'odid': wb_orders['odid'],
                'nmid': wb_orders['nmId'],
                'subject': wb_orders['subject'],
                'category': wb_orders['category'],
                'brand': wb_orders['brand'],
                'is_cancel': str(wb_orders['isCancel']),
                'cancel_dt': (lambda a,b,c: a if c != '0001-01-01T00:00:00'  else b) 
                    (datetime.strptime(wb_orders['cancel_dt'], "%Y-%m-%dT%H:%M:%S"), 
                    datetime.strptime('1940-01-01T00:00:00', "%Y-%m-%dT%H:%M:%S"), 
                    wb_orders['cancel_dt']),
            }
            self.env['wb.orders'].create(date)
        return True

    def create_from_wildberries_sales(self, wb):
        for wb_sales in wb:
            date = {
                'number': wb_sales['number'],
                'date': datetime.strptime(wb_sales['date'], "%Y-%m-%dT%H:%M:%S"),
                'last_change_date': wb_sales['lastChangeDate'],
                'last_change_date_and_time': datetime.strptime(wb_sales['lastChangeDate'], "%Y-%m-%dT%H:%M:%S"),
                'supplier_article': wb_sales['supplierArticle'],
                'tech_size': wb_sales['techSize'],
                'barcode': wb_sales['barcode'],
                'quantity': wb_sales['quantity'],
                'total_price': wb_sales['totalPrice'],
                'discount_percent': wb_sales['discountPercent'],
                'is_supply': wb_sales['isSupply'],
                'is_realization': wb_sales['isRealization'],
                'order_id': wb_sales['orderId'],
                'promo_code_discount': wb_sales['promoCodeDiscount'],
                'warehouse_name': wb_sales['warehouseName'],
                'country_name': wb_sales['countryName'],
                'oblast_okrug_name': wb_sales['oblastOkrugName'],
                'region_name': wb_sales['regionName'],
                'income_id': wb_sales['incomeID'],
                'sale_id': wb_sales['saleID'],
                'odid': wb_sales['odid'],
                'spp': wb_sales['spp'],
                'for_pay': wb_sales['forPay'],
                'finished_price': wb_sales['finishedPrice'],
                'price_with_disc': wb_sales['priceWithDisc'],
                'nmid': wb_sales['nmId'],
                'subject': wb_sales['subject'],
                'category': wb_sales['category'],
                'brand': wb_sales['brand'],
                'is_storno': wb_sales['IsStorno'],
            }
            self.env['wb.sales'].create(date)
        return True

    def create_from_wb_report_detail_by_period(self, wb):
        if wb == []:
            rrd_id = ''
            return rrd_id
        for wb_sales in wb:
            date = {
                'realizationreport_id': wb_sales['realizationreport_id'],
                'suppliercontract_code': wb_sales['suppliercontract_code'],
                'rr_dt': wb_sales['rr_dt'],
                'rr_dt_and_time': datetime.strptime(wb_sales['rr_dt'], "%Y-%m-%dT%H:%M:%S"),
                'rrd_id': wb_sales['rrd_id'],
                'gi_id': wb_sales['gi_id'],
                'subject_name': wb_sales['subject_name'],
                'nm_id': wb_sales['nm_id'],
                'brand_name': wb_sales['brand_name'],
                'sa_name': wb_sales['sa_name'],
                'ts_name': wb_sales['ts_name'],
                'barcode': wb_sales['barcode'],
                'doc_type_name': wb_sales['doc_type_name'],
                'quantity': wb_sales['quantity'],
                'nds': wb_sales['nds'],
                'cost_amount': wb_sales['cost_amount'],
                'retail_price': wb_sales['retail_price'],
                'retail_amount': wb_sales['retail_amount'],
                'retail_commission': wb_sales['retail_commission'],
                'sale_percent': wb_sales['sale_percent'],
                'commission_percent': wb_sales['commission_percent'],
                'customer_reward': wb_sales['customer_reward'],
                'supplier_reward': wb_sales['supplier_reward'],
                'office_name': wb_sales['office_name'],
                'supplier_oper_name': wb_sales['supplier_oper_name'],
                'order_dt': datetime.strptime(wb_sales['order_dt'], "%Y-%m-%dT%H:%M:%S"),
                'sale_dt': datetime.strptime(wb_sales['sale_dt'], "%Y-%m-%dT%H:%M:%S"),
                'shk_id': wb_sales['shk_id'],
                'retail_price_withdisc_rub': wb_sales['retail_price_withdisc_rub'],
                'for_pay_nds': wb_sales['for_pay_nds'],
                'delivery_amount': wb_sales['delivery_amount'],
                'return_amount': wb_sales['return_amount'],
                'delivery_rub': wb_sales['delivery_rub'],
                'gi_box_type_name': wb_sales['gi_box_type_name'],
                'product_discount_for_report': wb_sales['product_discount_for_report'],
                'supplier_promo': wb_sales['supplier_promo'],
                'supplier_spp': wb_sales['supplier_spp'],
            }
            self.env['wb.report.detail'].create(date)
        rrd_id = wb[-1]['rrd_id']
        
        return rrd_id

    @api.model
    def synchronize_events_cron(self, reportType, flag, args):
        """ Call by the cron. """
        today = datetime.today().date()
        print('крон    крон     крон !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        if args == 'hours':
            print('крон    крон     крон !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            if reportType == 'reportDetailByPeriod':
                update_date = today - timedelta(4)
                self = self.with_context(date_from=str(update_date), date_to=str(update_date),
                    db_cleanup_suffix='hours')
            else:
                yesterday = today - timedelta(1)
                self = self.with_context(date_from=str(yesterday), db_cleanup_suffix='hours')
        if args == 'months':
            """ if datetime.today().day != 4:
                return """
            if reportType == 'reportDetailByPeriod':
                date_from = today - timedelta(7)
                date_to = today - timedelta(5)
                self = self.with_context(date_from=str(date_from), date_to=str(date_to),
                    db_cleanup_suffix='months')
            else:
                date_from = today - timedelta(5)
                self = self.with_context(date_from=str(date_from), db_cleanup_suffix='months')
        try:
            resp = self.synchronize_events(reportType, flag)
            if resp.get("status") == "need_reset":
                _logger.info(
                    "Wildberries Synchro - Failed - NEED RESET  !")
            else:
                _logger.info(
                    "Wildberries Synchro - Done with status : %s  !", resp.get("status"))
        except Exception as e:
            _logger.info("Wildberries Synchro - Exception : %s !",
                         exception_to_unicode(e))
        _logger.info("Wildberries Synchro - Ended by cron")

    def synchronize_events(self, reportType, flag):
        """ This method should be called as the user to sync. """
        WBService = self.env['wb.service']
        client_id = WBService.get_client_id('wildberries')
        if not client_id or client_id == '':
            msg = _('Key is not specified wildberries')
            raise UserError(msg)

        res = self.update_events(reportType, flag)

        if flag == 1:
            update_date = datetime.strptime(self.env.context.get('date_from'), "%Y-%m-%d").date()
            r = datetime.today().date()
            while update_date != r:
                print(update_date)
                print(r)
                update_date += timedelta(1)
                res = self.with_context(date_from=str(update_date), no_delet=True).update_events(reportType, flag)

        if reportType == 'reportDetailByPeriod':
            rrd_id = res
            while rrd_id != '':
                rrd_id = self.update_events(reportType='reportDetailByPeriod', rrd_id=rrd_id)
            res = True

        return {
            "status": res and "need_refresh" or "no_new_event_from_wildberries",
            "url": ''
        }

    def update_events(self, reportType, flag=0, rrd_id=0):
        """ Synchronze events with wildberries : fetching, creating, updating, deleting, ... """
        try:
            all_event_from_wildberries = self.get_event_synchro_dict(reportType, flag, rrd_id)
        except requests.HTTPError as e:
            if e.response.status_code == 410:  # GONE, Wildberries is lost.
                # we need to force the rollback from this cursor, because it locks my res_users but I need to write in this tuple before to raise.
                self.env.cr.rollback()
                self.env.cr.commit()
            error_key = e.response.json()
            error_key = error_key.get('error', {}).get('message', 'nc')
            error_msg = _(
                "Wildberries is lost... the next synchro will be a full synchro. \n\n %s") % error_key
            raise self.env['res.config.settings'].get_config_warning(
                error_msg)

        wb = all_event_from_wildberries
        if reportType == 'incomes':
            self.deleting_data_in_wb_report(reportType, name_database = 'wb_incomes')
            self.create_from_wildberries_incomes(wb)
        elif reportType == 'stocks':
            self.deleting_data_in_wb_report(reportType, name_database = 'wb_stocks')
            self.create_from_wildberries_stocks(wb)
        elif reportType == 'orders':
            if not self.env.context.get('no_delet'):
                self.deleting_data_in_wb_report(reportType, name_database = 'wb_orders')
            self.create_from_wildberries_orders(wb)
        elif reportType == 'sales':
            if not self.env.context.get('no_delet'):
                self.deleting_data_in_wb_report(reportType, name_database = 'wb_sales')
            self.create_from_wildberries_sales(wb)
        elif reportType == 'reportDetailByPeriod':
            if self.env.context.get('db_cleanup_suffix') == 'months' and rrd_id == 0:
                self.deleting_data_in_wb_report(reportType, name_database = 'wb_report_detail')
            rrd_id = self.create_from_wb_report_detail_by_period(wb)
            return rrd_id

        return True
