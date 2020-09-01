from odoo import api, fields, models


class WBIncomes(models.Model):
    """ Delivery service """

    _name = 'wb.incomes'
    _description = 'Delivery service'

    incomeid = fields.Integer('Delivery number', readonly=True)
    number = fields.Integer('UPD number', readonly=True)
    date = fields.Datetime('Date of receipt', readonly=True)
    last_change_date = fields.Datetime('Date and time when the information was updated in service', readonly=True)
    supplier_article = fields.Char('Your article', readonly=True)
    tech_size = fields.Char('Size', readonly=True)
    barcode = fields.Char('Barcode', readonly=True)
    quantity = fields.Integer('Quantity', readonly=True)
    total_price = fields.Float('The price of UPD', readonly=True)
    date_close = fields.Datetime('Date of acceptance (closing) with us', readonly=True)
    warehouse_name = fields.Char('Warehouse name', readonly=True)
    nmid = fields.Integer('WB code', readonly=True)
    status = fields.Char('The current status of the delivery', readonly=True)