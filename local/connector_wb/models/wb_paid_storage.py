from odoo import fields, models


class WBPaidStorage(models.Model):
    """ Paid storage is a fact """

    _name = 'wb.paid.storage'
    _description = 'Paid storage is a fact'

    day_beg = fields.Datetime('Date-start of the storage period', readonly=True)
    day_end  = fields.Datetime('Date-end of the storage period', readonly=True)
    nmid = fields.Integer('WB code', readonly=True)
    tech_size = fields.Char('Size', readonly=True)
    days_on_site = fields.Char('Days on the site', readonly=True)
    stock = fields.Integer('Balance at the beginning of the period', readonly=True)
    sale_qty = fields.Float('The number of sold', readonly=True)
    sum_w = fields.Integer('Amount for storage, RUB', readonly=True)