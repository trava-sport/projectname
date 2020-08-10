# Copyright 2014-2018 Tecnativa - Pedro M. Baeza
# Copyright 2020 Tecnativa - Manuel Calero
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from psycopg2.extensions import AsIs

from odoo import api, fields, models, tools


class ProductsOnSale(models.Model):
    _name = "products.on.sale"
    _description = "Products On Sale"
    _auto = False
    """ _rec_name = "commission_id" """

    company_id = fields.Many2one("res.company", "Company", readonly=True)
    partner_id = fields.Many2one("res.partner", "Partner", readonly=True)
    categ_id = fields.Many2one("product.category", "Category of Product", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)
    barcode = fields.Char(string='Transferred', readonly=True)
    agreement_id = fields.Many2one(comodel_name='agreement', string='Agreement', readonly=True)
    transferred= fields.Float(string='Transferred', readonly=True,
        help="Quantity of the transferred product for sale.")
    paid = fields.Float(string='Paid', readonly=True,
        help="The quantity of the product for which payment was received from the Commission agent.")
    paid_sum = fields.Float(string='Paid sum', readonly=True,
        help="Received amount for the paid product")
    returned = fields.Float(string='Returned', readonly=True,
        help="Amount of refund from the Commission agent")
    remains = fields.Float(compute='_compute_remains', string='Remains',
        help="Quantity of goods on the Commission agent's balance")

    @api.depends('transferred', 'paid', 'returned')
    def _compute_remains(self):
        for remain in self:
            remain.remains = remain.transferred - remain.paid - remain.returned

    def _select(self):
        select_str = """
            SELECT MIN(sol.id) AS id,
            so.partner_id AS partner_id,
            so.company_id AS company_id,
            pt.categ_id AS categ_id,
            sol.product_id AS product_id,
            so.agreement_id AS agreement_id,
            pp.barcode AS barcode,
            SUM(sol.product_uom_qty) AS transferred,
            (SELECT
                    SUM(l.product_uom_qty)
                FROM commission_agent_report s
                LEFT JOIN commission_agent_report_line l ON (l.report_id = s.id)
                WHERE s.state IN ('sale', 'done')
                 and l.product_id = sol.product_id) AS paid,
            (SELECT
                    SUM(l.amount) 
                FROM commission_agent_report s
                LEFT JOIN commission_agent_report_line l ON (l.report_id = s.id)
                WHERE s.state IN ('sale', 'done')
                 and l.product_id = sol.product_id) AS paid_sum,
            (SELECT
                    SUM(l.quantity)
                FROM account_move s
                LEFT JOIN account_move_line l ON (l.move_id = s.id)
                LEFT JOIN agreement g ON (s.agreement_id= g.id)
                WHERE s.state IN ('posted')
                AND s.type IN ('out_refund')
                and g.agreement_type_id IN ('commission')
                and l.product_id = sol.product_id) AS returned
        """
        return select_str

    def _from(self):
        from_str = """
            sale_order so
            LEFT JOIN sale_order_line sol ON (sol.order_id = so.id)
            LEFT JOIN agreement ag ON (so.agreement_id= ag.id)
            LEFT JOIN product_product pp ON pp.id = sol.product_id
            INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN res_partner rp ON so.partner_id = rp.id
        """
        return from_str

    def _where(self):
        where_str = """
            WHERE ag.agreement_type_id IN ('commission')
            AND so.state IN ('sale', 'done')
        """
        return where_str

    def _group_by(self):
        group_by_str = """
            GROUP BY so.partner_id,
            so.company_id,
            pt.categ_id,
            sol.product_id,
            so.agreement_id,
            pp.barcode
        """
        return group_by_str

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            "CREATE or REPLACE VIEW %s AS ( %s FROM ( %s ) %s %s )",
            (
                AsIs(self._table),
                AsIs(self._select()),
                AsIs(self._from()),
                AsIs(self._where()),
                AsIs(self._group_by()),
            ),
        )
