# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
import time
import json
import logging

import requests
from werkzeug import urls

from odoo import api, fields, models, registry, _
from odoo.exceptions import UserError
from odoo.http import request


_logger = logging.getLogger(__name__)

TIMEOUT = 20

# FIXME : this needs to become an AbstractModel, to be inhereted by wildberries_service


class WBService(models.TransientModel):
    _name = 'wb.service'
    _description = 'Wildberries Service'

    # @api.model
    # def _do_request(self, uri, params={}, headers={}, type='POST', preuri="https://suppliers-stats.wildberries.ru"):
    #     """ Execute the request to Wildberries API. Return a tuple ('HTTP_CODE', 'HTTP_RESPONSE')
    #         :param uri : the url to contact
    #         :param params : dict or already encoded parameters for the request to make
    #         :param headers : headers of request
    #         :param type : the method to use to make the request
    #         :param preuri : pre url to prepend to param uri.
    #     """
    #     _logger.debug("Uri: %s - Type : %s - Headers: %s - Params : %s !", (uri, type, headers, params))

    #     ask_time = fields.Datetime.now()
    #     try:
    #         if type.upper() in ('GET', 'DELETE'):
    #             res = requests.request(type.lower(), preuri + uri, params=params, timeout=TIMEOUT)
    #         elif type.upper() in ('POST', 'PATCH', 'PUT'):
    #             res = requests.request(type.lower(), preuri + uri, data=params, headers=headers, timeout=TIMEOUT)
    #         else:
    #             raise Exception(_('Method not supported [%s] not in [GET, POST, PUT, PATCH or DELETE]!') % (type))
    #         res.raise_for_status()
    #         status = res.status_code

    #         if int(status) in (204, 404):  # Page not found, no response
    #             response = False
    #         else:
    #             response = res.json()

    #         try:
    #             ask_time = datetime.strptime(res.headers.get('date'), "%a, %d %b %Y %H:%M:%S %Z")
    #         except:
    #             pass
    #     except requests.HTTPError as error:
    #         if error.response.status_code in (204, 404):
    #             status = error.response.status_code
    #             response = ""
    #         else:
    #             _logger.exception("Bad wildberries request : %s !", error.response.content)
    #             if error.response.status_code in (400, 401, 410):
    #                 raise error
    #             raise self.env['res.config.settings'].get_config_warning(_("Something went wrong with your request to wildberries. Try again in 30 seconds"))
    #     return (status, response, ask_time)

    @api.model
    def _do_request(self, uri, params={}, headers={}, reportType = 'None', type='POST', preuri="https://suppliers-stats.wildberries.ru"):
        """ Execute the request to Wildberries API. Return a tuple ('HTTP_CODE', 'HTTP_RESPONSE')
            :param uri : the url to contact
            :param params : dict or already encoded parameters for the request to make
            :param headers : headers of request
            :param type : the method to use to make the request
            :param preuri : pre url to prepend to param uri.
        """
        _logger.debug("Uri: %s - Type : %s - Headers: %s - Params : %s !", (uri, type, headers, params))

        ask_time = fields.Datetime.now()
        while True:
            try:
                if type.upper() in ('GET', 'DELETE'):
                    res = requests.request(type.lower(), preuri + uri, params=params, timeout=TIMEOUT)
                elif type.upper() in ('POST', 'PATCH', 'PUT'):
                    res = requests.request(type.lower(), preuri + uri, data=params, headers=headers, timeout=TIMEOUT)
                else:
                    raise Exception(_('Method not supported [%s] not in [GET, POST, PUT, PATCH or DELETE]!') % (type))
                
                if reportType in ('orders', 'sales'):
                    if params['flag'] == 1 and res.status_code != 200:
                        _logger.info("Ошибка, Код ответа: %s", res.status_code)
                        time.sleep(10)

                        # Попробуем снова на следующей итерации цикла
                        continue

                res.raise_for_status()
                status = res.status_code

                if int(status) in (204, 404):  # Page not found, no response
                    response = False
                else:
                    response = res.json()

                try:
                    ask_time = datetime.strptime(res.headers.get('date'), "%a, %d %b %Y %H:%M:%S %Z")
                except:
                    pass
            except requests.HTTPError as error:
                if error.response.status_code in (204, 404):
                    status = error.response.status_code
                    response = ""
                else:
                    _logger.exception("Bad wildberries request : %s !", error.response.content)
                    if error.response.status_code in (400, 401, 410):
                        raise error
                    raise self.env['res.config.settings'].get_config_warning(_("Something went wrong with your request to wildberries. Try again in 30 seconds"))
            return (status, response, ask_time)

    # TODO : remove me, it is only used in wildberries. Make connector_wb use the constants
    @api.model
    def get_client_id(self, service):
        return self.env['ir.config_parameter'].sudo().get_param('%s_client_secret' % (service,), default=False)
