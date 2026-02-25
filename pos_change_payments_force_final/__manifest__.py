{
    "name": "POS Change Payments - Force Final (Odoo 19)",
    "version": "19.0.1.3.0",
    "category": "Point of Sale",
    "author": "Mouad Lyaazale",
    "price": 20.99,
    "currency": "EUR",
    "summary": "Force edit POS payment lines for reporting even if posted/invoiced (SQL-only).",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/pos_order_views.xml",
        "wizard/wizard_views.xml"
    ],
    "installable": True,
    "application": False
}
