from odoo import api, fields, models


class WBStocks(models.Model):
    """ Delivery service """

    _name = 'wb.stocks'
    _description = 'Stocks service'

    last_change_date = fields.Datetime('Date and time when the information was updated in service', readonly=True)
    supplier_article = fields.Char('Your article', readonly=True)
    tech_size = fields.Char('Size', readonly=True)
    barcode = fields.Char('Barcode', readonly=True)
    quantity = fields.Integer('Quantity available for sale', readonly=True)
    is_supply = fields.Char('Supply contract', readonly=True)
    is_realization = fields.Char('Sales agreement', readonly=True)
    quantity_full = fields.Integer('Quantity full', readonly=True)
    quantity_not_in_orders = fields.Integer('Qty not in order', readonly=True)
    warehouse_name = fields.Char('Warehouse name', readonly=True)
    in_way_to_client = fields.Integer('On the way to the client (pieces)', readonly=True)
    in_way_from_client = fields.Integer('On the way from the client (pieces)', readonly=True)
    nmid = fields.Char('WB code', readonly=True)
    subject = fields.Char('Subject', readonly=True)
    category = fields.Char('Category', readonly=True)
    days_on_site = fields.Integer('Number of days on the site', readonly=True)
    brand = fields.Char('Brand', readonly=True)
    sccode = fields.Char('Contract code', readonly=True)
    price = fields.Integer('Price', readonly=True)
    discount = fields.Integer('Discount', readonly=True)