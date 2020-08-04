# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import re

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.tools import float_compare


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    sale_order_ids = fields.Many2many('commission.agent.report', 'commission_agent_transaction_rel', 'transaction_id', 'commission_agent_id',
                                      string='Commission Agent Report', copy=False, readonly=True)
    
