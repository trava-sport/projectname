# Copyright 2014-2020 Tecnativa - Pedro M. Baeza
# Copyright 2020 Tecnativa - Manuel Calero
{
    "name": "Sales commissions",
    "version": "13.0.1.0.0",
    "author": "Sparta",
    "category": "Sales Management",
    "license": "AGPL-3",
    "depends": ["account", "product", "sale_management"],
    "website": "https://github.com/OCA/commission",
    "development_status": "Mature",
    "maintainers": ["pedrobaeza"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_commission_view.xml",
    ],
    "installable": True,
}
