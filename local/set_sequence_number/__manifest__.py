# -*- coding: utf-8 -*-

{
    "name": "Set sequence number to One2many",
    "summary": "Set Sequence number to sale line, purchase line and stock moves",
    "version": "1.0.1",
    "author": "Conceiver Tech",
    "website" : "conceivertech@gmail.com",
    "description": """
""",
    "license": "Other proprietary",
    "category": "sale",
    'license': 'OPL-1',
    "depends": [
        "purchase",
        "sale_stock",
    ],
    'images': ['static/description/banner.png'],
    "data": [
        "view/purchase_view.xml",
        "view/sale_view.xml",
        "view/stock_view.xml",
    ],
    "installable": True,
}
