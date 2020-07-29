# -*- coding: utf-8 -*-
from odoo import models, api, fields


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sequence_ref = fields.Integer('No.', compute="_sequence_ref")

    def _prepare_stock_moves(self, picking):
        self.ensure_one()
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for val in res:
            if val.get('product_id') == self.product_id.id:
                val.update({'sequence_ref': self.sequence_ref})
        return res

    @api.depends('order_id.order_line', 'order_id.order_line.product_id')
    def _sequence_ref(self):
        no = 0
        for line in self:
            no += 1
            line.sequence_ref = no