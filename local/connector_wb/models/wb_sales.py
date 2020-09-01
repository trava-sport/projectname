from odoo import api, fields, models


class WBSales(models.Model):
    """ Sales service """

    _name = 'wb.sales'
    _description = 'Sales service'

    number = fields.Integer('Document number', readonly=True)
    date = fields.Datetime('Date of sale', readonly=True)
    last_change_date = fields.Date('Date when the information was updated in service', readonly=True)
    last_change_date_and_time = fields.Datetime('Date and time when the information was updated in service', readonly=True)
    supplier_article = fields.Char('Your article', readonly=True)
    tech_size = fields.Char('Size', readonly=True)
    barcode = fields.Char('Barcode', readonly=True)
    quantity = fields.Integer('Quantity', readonly=True)
    total_price = fields.Float('Initial retail price of the product', readonly=True)
    discount_percent = fields.Integer('An agreed discount on the product', readonly=True)
    is_supply = fields.Char('Supply contract', readonly=True)
    is_realization = fields.Char('Sales agreement', readonly=True)
    order_id = fields.Char('source order number', readonly=True,
        help='"order Number" from "Orders" service')
    promo_code_discount = fields.Integer('Approved promo code', readonly=True)
    warehouse_name = fields.Char('Shipment warehouse', readonly=True)
    country_name = fields.Char('Country', readonly=True)
    oblast_okrug_name = fields.Char('District', readonly=True)
    region_name = fields.Char('Region', readonly=True)
    income_id = fields.Integer('Delivery number', readonly=True)
    sale_id = fields.Char('the unique identifier of the sale/return', readonly=True,
        help='SXXXXXXXXXX-sale, RXXXXXXXXXX — refund, DXXXXXXXXXXX-surcharge')
    odid = fields.Char('Unique ID of the order item', readonly=True)
    spp = fields.Integer('agreed regular customer discount(SPP)', readonly=True)
    for_pay = fields.Float('To transfer to the supplier', readonly=True)
    finished_price = fields.Integer('The actual price from the order', readonly=True,
        help='the actual price from the order (including all discounts, including from the world Bank)')
    price_with_disc = fields.Integer('Price', readonly=True,
        help='the price from which remuneration is calcu forpay provider (including all agreed terms discounts)')
    nmid = fields.Char('WB code', readonly=True)
    subject = fields.Char('Subject', readonly=True)
    category = fields.Char('Category', readonly=True)
    brand = fields.Char('Brand', readonly=True)
    is_storno = fields.Integer('Storno', readonly=True,
        help='1 - sale is reversed, 0 - is not reversed')