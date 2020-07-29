from odoo import _, api, exceptions, fields, models


class CommissionAgentReport(models.Model):
    _name = "сommission.agent.report"
    _description = "Commission agent's report"


    number = fields.Integer(string='Report number', required=True, track_visibility='onchange')
    signature_date = fields.Date(required=True, track_visibility='onchange')
    partner_id = fields.Many2one(
        'res.partner', string='Partner', required=True, ondelete='restrict',
        domain=[('parent_id', '=', False)], track_visibility='onchange')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get())
    start_date = fields.Date(required=True, track_visibility='onchange')
    end_date = fields.Date(required=True, track_visibility='onchange')
    agreement_id = fields.Many2one(
        comodel_name='agreement', string='Agreement', ondelete='restrict',
        track_visibility='onchange', readonly=True, required=True, copy=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    incoming_number = fields.Integer(string='Report number', required=True, track_visibility='onchange')
    incoming_signature_date = fields.Date(required=True, track_visibility='onchange')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=5)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', tracking=4)
    commission_agent_remuneration = fields.Monetary(string='Commission agents remuneration', store=True, readonly=True, compute='_amount_remuneration', tracking=4)
    amount_committee = fields.Monetary(string='Amount of the Committee', store=True, readonly=True, compute='_amount_remuneration', tracking=4)
    quantity = fields.Integer(string='Quantity', store=True, readonly=True, compute='_amount_quantity', tracking=4)
    commission_line = fields.One2many('сommission.agent.report.line', 'order_id', string='Commission Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    commission_id = fields.Many2one(string="Commission", comodel_name="sale.commission")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)

    @api.constrains("start_date", "end_date")
    def _check_amounts(self):
        for report in self:
            if report.end_date < report.start_date:
                raise exceptions.ValidationError(
                    _("The start date of the period must be earlier than the end date of the period.")
                )

    @api.depends('commission_line.amount')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.commission_line:
                amount_untaxed += line.amount
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.depends('commission_line.remuneration')
    def _amount_remuneration(self):
        for line in self:
            for remuneration in line.commission_line.remuneration:
                line.commission_agent_remuneration += remuneration
            line.amount_committee = line.amount_total - line.commission_agent_remuneration

    @api.depends('commission_line.product_uom_qty')
    def _amount_quantity(self):
        for line in self:
            for quantity in line.commission_line.product_uom_qt:
                line.commission_agent_remuneration += quantity


class CommissionAgentReportLine(models.Model):
    _inherit = "sale.commission.line.mixin"
    _name = "сommission.agent.report.line"
    _description = "Commission agent's report line"
    _order = 'order_id, sequence, id'
    _check_company_auto = True


    product_id = fields.Many2one(
        'product.product', string='Product', domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    report_id = fields.Many2one('сommission.agent.report', string='Link to the report', required=True, ondelete='cascade', index=True, copy=False)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    amount = fields.Monetary(compute='_compute_amount', string='Amount', readonly=True, store=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.amount = line.product_uom_qty * line.price_unit

    def _compute_remuneration(self):
        for line in self:
            line.remuneration = line._get_commission_amount(
                line.commission_id,
                line.amount,
                line.product_id,
                line.product_uom_qty,
            )

    @api.depends('product_uom_qty', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.compute_all(price, line.report_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.report_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'amount': taxes['total_excluded'],
            })