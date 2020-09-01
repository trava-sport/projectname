from odoo import api, fields, models


class WBOrders(models.Model):
    """ Orders service """

    _name = 'wb.orders'
    _description = 'Orders service'

    number = fields.Char('Order number', readonly=True)
    date = fields.Datetime('Date orders', readonly=True)
    last_change_date = fields.Date('Date when the information was updated in service', readonly=True)
    last_change_date_and_time = fields.Datetime('Date and time when the information was updated in service', readonly=True)
    supplier_article = fields.Char('Your article', readonly=True)
    tech_size = fields.Char('Size', readonly=True)
    barcode = fields.Char('Barcode', readonly=True)
    quantity = fields.Integer('Quantity', readonly=True)
    total_price = fields.Float('Price up to the agreed discount / promo/spp', readonly=True)
    discount_percent = fields.Integer('The approved final discount', readonly=True)
    warehouse_name = fields.Char('Shipment warehouse', readonly=True)
    oblast = fields.Char('Area', readonly=True)
    income_id = fields.Integer('Delivery number', readonly=True)
    odid = fields.Char('Unique ID of the order item', readonly=True)
    nmid = fields.Integer('WB code', readonly=True)
    subject = fields.Char('Subject', readonly=True)
    category = fields.Char('Category', readonly=True)
    brand = fields.Char('Brand', readonly=True)
    is_cancel = fields.Char('indicates whether the order was canceled', readonly=True,
        help='0 - there was no cancellation, 1 - there was a cancellation')
    cancel_dt = fields.Datetime('Date of order cancellation', readonly=True)