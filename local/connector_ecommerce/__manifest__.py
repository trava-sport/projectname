# -*- coding: utf-8 -*-
# © 2013-2016 Camptocamp SA
# © 2013-2016 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{'name': 'Connector for E-Commerce',
 'version': '12.0.1.1.0',
 'category': 'Hidden',
 'author': "Camptocamp,Akretion,Odoo Community Association (OCA)",
 'website': 'http://odoo-connector.com',
 'license': 'AGPL-3',
 'depends': [
     'connector',
     'sale_automatic_workflow_payment_mode',
     'sale_exception',
     'delivery',
 ],
 'data': [
     'security/ir.model.access.csv',
     'wizard/sale_ignore_cancel_view.xml',
     'views/sale_view.xml',
     'views/stock_view.xml',
     'views/payment_mode_view.xml',
     'views/invoice_view.xml',
 ],
 'installable': True,
 }
