# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Wildberries connector',
    'version': '1.0',
    'category': 'Tools',
    'description': "",
    'depends': ['sale_management'],
    'qweb': ['static/src/xml/*.xml'],
    'data': [
        'data/wb_data.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/wb_incomes.xml',
        'views/wb_orders.xml',
        'views/wb_paid_storage.xml',
        'views/wb_sales.xml',
        'views/wb_report_detail_by_period.xml',
        'views/wb_stocks.xml',
        'views/wb_price.xml',
        'wizard/updat_wb_reports_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
