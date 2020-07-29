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
    commission_agent_remuneration = fields.Monetary(string='Commission agents remuneration', store=True, readonly=True, compute='_amount_all', tracking=4)
    amount_committee = fields.Monetary(string='Amount of the Committee', store=True, readonly=True, compute='_amount_all', tracking=4)
    quantity = fields.Integer(string='Quantity', store=True, readonly=True, compute='_amount_all', tracking=4)
    commission_line = fields.One2many('сommission.agent.report.line', 'order_id', string='Commission Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)


class CommissionAgentReportLine(models.Model):
    _name = "сommission.agent.report.line"
    _description = "Commission agent's report line"
    _order = 'order_id, sequence, id'
    _check_company_auto = True


    line_number = fields.Integer(string='Report number', required=True, track_visibility='onchange')
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    amount = fields.Monetary(compute='_compute_amount', string='Amount', readonly=True, store=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.amount = line.product_uom_qty * line.price_unit