# -*- coding: utf-8 -*-
from odoo import models, api, fields


class StockRule(models.Model):
    _inherit = 'stock.rule'

    sequence_ref = fields.Integer('No.', help="Gives the sequence order when displaying a list of sales order lines.")

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        if values.get('sequence_ref', False):
            result['sequence_ref'] = values['sequence_ref']
        return result

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = "sequence"

    sequence_ref = fields.Integer('No.', compute="_sequence_ref")

    def _prepare_procurement_values(self, group_id=False):
        self.ensure_one()
        vals = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        vals.update({'sequence_ref':self.sequence_ref})
        return vals

    @api.depends('order_id.order_line', 'order_id.order_line.product_id')
    def _sequence_ref(self):
        no = 0
        for line in self:
            no += 1
            line.sequence_ref = no
