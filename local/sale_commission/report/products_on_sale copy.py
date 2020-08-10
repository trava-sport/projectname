# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    agreement_id = fields.Many2one(
        comodel_name='agreement', string='Agreement', ondelete='restrict',
        track_visibility='onchange', required=True, copy=False)
    transferred= fields.Float(compute='_compute_product_margin_fields_values', string='Transferred',
        help="Quantity of the transferred product for sale.")
    paid = fields.Float(compute='_compute_product_margin_fields_values', string='Paid',
        help="The quantity of the product for which payment was received from the Commission agent.")
    paid_sum = fields.Float(compute='_compute_product_margin_fields_values', string='Paid sum',
        help="Received amount for the paid product")
    returned = fields.Float(compute='_compute_product_margin_fields_values', string='Returned',
        help="Amount of refund from the Commission agent")
    remains = fields.Float(compute='_compute_product_margin_fields_values', string='Remains',
        help="Quantity of goods on the Commission agent's balance")

    def _compute_product_margin_fields_values(self, field_names=None):
        res = {}
        if field_names is None:
            field_names = []
        for val in self:
            res[val.id] = {}
            if "force_company" in self.env.context:
                company_id = self.env.context['force_company']
            else:
                company_id = self.env.company.id

            #Cost price is calculated afterwards as it is a property
            self.env['account.move.line'].flush(['price_unit', 'quantity', 'balance', 'product_id', 'display_type'])
            self.env['account.move'].flush(['state', 'invoice_payment_state', 'type', 'invoice_date', 'company_id'])
            self.env['sale.order.line'].flush(['product_uom_qty'])
            self.env['commission_agent_report_line'].flush(['product_uom_qty', 'amount'])
            sqlstr = """
                SELECT
                    SUM(l.product_uom_qty) AS transferred_qty
                FROM sale_order s
                LEFT JOIN sale_order_line l ON (l.order_id = s.id)
                LEFT JOIN agreement g ON (s.agreement_id= g.id)
                WHERE l.product_id = %s
                and g.agreement_type_id IN %s
                AND i.company_id = %s
                AND s.state IN %s
                """
            agreement_type = ('commission')
            order_state = ('sale', 'done')
            self.env.cr.execute(sqlstr, (val.id, agreement_type, company_id, order_state))
            result = self.env.cr.fetchall()[0]
            res[val.id]['transferred'] = result[0] and result[0] or 0.0
            ctx = self.env.context.copy()
            ctx['force_company'] = company_id
            sqlstr = """
                SELECT
                    SUM(l.product_uom_qty) AS paid_qty,
                    SUM(l.amount) AS paid_sum
                FROM commission_agent_report s
                LEFT JOIN commission_agent_report_line l ON (l.report_id = s.id)
                WHERE l.product_id = %s
                AND i.company_id = %s
                AND s.state IN %s
                """
            report_state = ('sale', 'done')
            self.env.cr.execute(sqlstr, (val.id, company_id, report_state))
            result = self.env.cr.fetchall()[0]
            res[val.id]['paid'] = result[0] and result[0] or 0.0
            res[val.id]['paid_sum'] = result[1] and result[1] or 0.0
            ctx = self.env.context.copy()
            ctx['force_company'] = company_id
            sqlstr = """
                SELECT
                    SUM(l.quantity) AS returned_qty
                FROM account_move s
                LEFT JOIN account_move_line l ON (l.move_id = s.id)
                LEFT JOIN agreement g ON (s.agreement_id= g.id)
                WHERE l.product_id = %s
                AND i.company_id = %s
                AND s.state IN %s
                AND s.type IN %s
                and g.agreement_type_id IN %s
                """
            invoice_state = ('posted')
            type_invoice = ('out_refund')
            agreement_type = ('commission')
            self.env.cr.execute(sqlstr, (val.id, company_id, invoice_state, type_invoice, agreement_type))
            result = self.env.cr.fetchall()[0]
            res[val.id]['returned'] = result[0] and result[0] or 0.0

            res[val.id]['remains'] = res[val.id]['transferred'] - res[val.id]['paid'] - res[val.id]['returned']
            for k, v in res[val.id].items():
                setattr(val, k, v)
        return res
