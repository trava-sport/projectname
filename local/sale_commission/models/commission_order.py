# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.exceptions import UserError


class CommissionAgentReport(models.Model):
    _inherit = "commission.agent.report"

    @api.model
    def _default_warehouse_id(self):
        company = self.env.company.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    incoterm = fields.Many2one(
        'account.incoterms', 'Incoterm',
        help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_default_warehouse_id, check_company=True)
    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group', copy=False)

    @api.model
    def create(self, vals):
        if 'warehouse_id' not in vals and 'company_id' in vals and vals.get('company_id') != self.env.company.id:
            vals['warehouse_id'] = self.env['stock.warehouse'].search([('company_id', '=', vals.get('company_id'))], limit=1).id
        return super(CommissionAgentReport, self).create(vals)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            warehouse_id = self.env['ir.default'].get_model_defaults('sale.order').get('warehouse_id')
            self.warehouse_id = warehouse_id or self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)

    def _prepare_invoice(self):
        invoice_vals = super(CommissionAgentReport, self)._prepare_invoice()
        invoice_vals['invoice_incoterm_id'] = self.incoterm.id
        return invoice_vals


class CommissionAgentReportLine(models.Model):
    _inherit = 'commission.agent.report.line'

    product_packaging = fields.Many2one( 'product.packaging', string='Package', default=False, check_company=True)
    route_id = fields.Many2one('stock.location.route', string='Route', domain=[('sale_selectable', '=', True)], ondelete='restrict', check_company=True)
    move_ids = fields.One2many('stock.move', 'sale_line_id', string='Stock Moves')
    product_type = fields.Selection(related='product_id.type')

    @api.depends('report_id.state')
    def _compute_invoice_status(self):
        super(CommissionAgentReportLine, self)._compute_invoice_status()
        for line in self:
            # We handle the following specific situation: a physical product is partially delivered,
            # but we would like to set its invoice status to 'Fully Invoiced'. The use case is for
            # products sold by weight, where the delivered quantity rarely matches exactly the
            # quantity ordered.
            if line.report_id.state == 'done'\
                    and line.invoice_status == 'no'\
                    and line.product_id.type in ['consu', 'product']\
                    and line.move_ids \
                    and all(move.state in ['done', 'cancel'] for move in line.move_ids):
                line.invoice_status = 'invoiced'

    @api.depends('move_ids')
    def _compute_product_updatable(self):
        for line in self:
            if not line.move_ids.filtered(lambda m: m.state != 'cancel'):
                super(CommissionAgentReportLine, line)._compute_product_updatable()
            else:
                line.product_updatable = False

    @api.onchange('product_packaging')
    def _onchange_product_packaging(self):
        if self.product_packaging:
            return self._check_package()

    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = super(CommissionAgentReportLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        date_planned = self.report_id.date_order\
            + timedelta(days=self.customer_lead or 0.0) - timedelta(days=self.report_id.company_id.security_lead)
        values.update({
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned,
            'route_ids': self.route_id,
            'warehouse_id': self.report_id.warehouse_id or False,
            'partner_id': self.report_id.partner_shipping_id.id,
            'company_id': self.report_id.company_id,
        })
        for line in self.filtered("report_id.commitment_date"):
            date_planned = fields.Datetime.from_string(line.report_id.commitment_date) - timedelta(days=line.report_id.company_id.security_lead)
            values.update({
                'date_planned': fields.Datetime.to_string(date_planned),
            })
        return values

    def _check_package(self):
        default_uom = self.product_id.uom_id
        pack = self.product_packaging
        qty = self.product_uom_qty
        q = default_uom._compute_quantity(pack.qty, self.product_uom)
        # We do not use the modulo operator to check if qty is a mltiple of q. Indeed the quantity
        # per package might be a float, leading to incorrect results. For example:
        # 8 % 1.6 = 1.5999999999999996
        # 5.4 % 1.8 = 2.220446049250313e-16
        if (
            qty
            and q
            and float_compare(
                qty / q, float_round(qty / q, precision_rounding=1.0), precision_rounding=0.001
            )
            != 0
        ):
            newqty = qty - (qty % q) + q
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _("This product is packaged by %.2f %s. You should sell %.2f %s.") % (pack.qty, default_uom.name, newqty, self.product_uom.name),
                },
            }
        return {}
