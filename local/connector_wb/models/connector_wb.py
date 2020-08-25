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

    def get_event_synchro_dict(self, reportType='None'):
        """ Returns events on the 'primary' calendar from google cal.
            :returns dict where the key is the google_cal event id, and the value the details of the event,
                    defined at https://developers.google.com/google-apps/calendar/v3/reference/events/list
        """
        token = self.env['wb.service'].get_client_id('wildberries')

        params = {
            'key': token,
        }

        if reportType == 'incomes' or reportType == 'stocks':
            params['dateFrom'] = self.env.context.get('date')
        else:
            params['timeMin'] = self.get_minTime().strftime(
                "%Y-%m-%dT%H:%M:%S.%fz")

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        url = "/api/v1/supplier/%s" % reportType

        status, content, ask_time = self.env['wb.service']._do_request(
            url, params, headers, type='GET')

        return content

    def deleting_data_in_wb_report(self, name_database):
        cr = self._cr
        query = "DELETE FROM %s" % name_database
        cr.execute(query)

    def create_from_wildberries_incomes(self, wb):
        for wb_incomes in wb:
            date = {
                'incomeid': wb_incomes['incomeId'],
                'number': wb_incomes['number'],
                'date': wb_incomes['date'],
                'last_change_date': wb_incomes['lastChangeDate'],
                'supplier_article': wb_incomes['supplierArticle'],
                'barcode': wb_incomes['barcode'],
                'quantity': wb_incomes['quantity'],
                'total_price': wb_incomes['totalPrice'],
                'date_close': wb_incomes['dateClose'],
                'warehouse_name': wb_incomes['warehouseName'],
                'nmid': wb_incomes['nmId'],
                'status': wb_incomes['status'],
            }
            self.env['wb.incomes'].create(date)
        return True

    def create_from_wildberries_stocks(self, wb):
        for wb_stocks in wb:
            date = {
                'last_change_date': wb_stocks['lastChangeDate'],
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

    @api.model
    def synchronize_events_cron(self):
        """ Call by the cron. """
        try:
            resp = self.synchronize_events(reportType='None')
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

    def synchronize_events(self, reportType='None'):
        """ This method should be called as the user to sync. """
        WBService = self.env['wb.service']
        client_id = WBService.get_client_id('wildberries')
        if not client_id or client_id == '':
            msg = _('Key is not specified wildberries')
            raise UserError(msg)

        res = self.update_events(reportType)

        return {
            "status": res and "need_refresh" or "no_new_event_from_google",
            "url": ''
        }

    def update_events(self, reportType):
        """ Synchronze events with wildberries : fetching, creating, updating, deleting, ... """
        try:
            all_event_from_wildberries = self.get_event_synchro_dict(reportType=reportType)
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

        # clearing the database before updating
        if reportType == 'incomes':
            self.deleting_data_in_wb_report(name_database = 'wb_incomes')
        elif reportType == 'stocks':
            self.deleting_data_in_wb_report(name_database = 'wb_stocks')

        wb = all_event_from_wildberries
        if reportType == 'incomes':
            self.create_from_wildberries_incomes(wb)
        elif reportType == 'stocks':
            self.create_from_wildberries_stocks(wb)

        return True
