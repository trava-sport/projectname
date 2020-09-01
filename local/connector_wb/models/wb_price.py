from odoo import api, fields, models


class WBPrice(models.Model):
    """ Pricing on wildberries """

    _name = 'wb.price'
    #_inherits = {'product.template': 'barcode', 'wb.report.detail': 'barcode_1'}
    _description = 'Pricing on wildberries'

    brand = fields.Char('Brand')
    subject = fields.Char('Subject')
    collection = fields.Char('Collection')
    supplier_article = fields.Char('Suppliers article')
    nomenclature = fields.Char('Nomenclature (Code 1C)')
    last_barcode = fields.Char('Last barcode')
    number_days_site = fields.Integer('Number of days on the site')
    unmarketable = fields.Char('Unmarketable')
    date_Unmarketable = fields.Date('Date of appearance of the illiquid')
    turnover = fields.Char('Turnover')
    remainder_goods = fields.Integer('The remainder of the goods (units)')
    current_retail_price = fields.Integer('Current retail price(before discount)')
    new_retail_price = fields.Integer('New retail price (before discount)')
    current_discount_site = fields.Integer('Current discount on the site,%')
    recommended_discount = fields.Integer('Recommended discount,%')
    agreed_discount = fields.Integer('The agreed discount,%')
    current_promo_code_discount = fields.Integer('Current promo code discount,%')
    new_promo_code_discount = fields.Integer('New promo code discount,%')
    current_price_discounts = fields.Integer('Current price with discounts', compute='_compute_current_price_discounts', store=True)
    current_price_disc_promo_code = fields.Integer('Current price with discounts and promo codes', compute='_compute_current_price_disc_promo_code', store=True)
    new_price_discounts = fields.Integer('New price with discounts', compute='_compute_new_price_discounts', store=True)
    new_price_disc_promo_code = fields.Integer('New price with discounts and promo codes', compute='_compute_new_price_disc_promo_code', store=True)
    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price', store=True,
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
        In FIFO: value of the last unit that left the stock (automatically computed).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""")
    current_net_profit = fields.Float('Current net profit', compute='_compute_current_net_profit', store=True)
    new_net_profit = fields.Float('New net profit', compute='_compute_new_net_profit', store=True)
    #price_per_piece = fields.Integer('Price per piece', compute='_compute_standard_price', store=True)
    
    
    def _compute_standard_price(self):
        product_id = self.env['product.product'].search([('barcode', '=', self.last_barcode)], limit=None).id
        products = self.env['ir.property'].search([('res_id', '=', 'product.product,%s' % product_id)], limit=None)
        self.standard_price = products.value_float

    @api.depends('current_retail_price', 'current_discount_site')
    def _compute_current_price_discounts(self):
        self.current_price_discounts = self.current_retail_price - (self.current_retail_price * 
            (self.current_discount_site / 100))

    @api.depends('current_price_discounts', 'current_promo_code_discount')
    def _compute_current_price_disc_promo_code(self):
        self.current_price_disc_promo_code = self.current_price_discounts - (self.current_price_discounts * 
            (self.current_promo_code_discount / 100))

    @api.depends('current_retail_price', 'agreed_discount')
    def _compute_new_price_discounts(self):
        self.new_price_discounts = self.current_retail_price - (self.current_retail_price * 
            (self.agreed_discount / 100))

    @api.depends('new_price_discounts', 'new_promo_code_discount')
    def _compute_new_price_disc_promo_code(self):
        self.new_price_disc_promo_code = self.new_price_discounts - (self.new_price_discounts * 
            (self.new_promo_code_discount / 100))

    @api.depends('current_price_disc_promo_code', 'standard_price')
    def _compute_current_net_profit(self):
        self.current_net_profit = self.current_price_disc_promo_code - (self.current_price_disc_promo_code * 
            0.15) - self.standard_price - 66

    @api.depends('new_price_disc_promo_code', 'standard_price')
    def _compute_new_net_profit(self):
        self.new_net_profit = self.new_price_disc_promo_code - (self.new_price_disc_promo_code * 
            0.15) - self.standard_price - 66