# -*- coding: utf-8 -*-
from odoo import models, api, fields

class StockMove(models.Model):
    _inherit = 'stock.move'

    sequence_ref = fields.Integer('No.', compute="_sequence_ref")

    @api.depends('picking_id.move_lines', 'picking_id.move_lines.product_id')
    def _sequence_ref(self):
        count = 0
        for move in self:
            count += 1
            move.sequence_ref = count

