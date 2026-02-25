{
    "name": "Invoice MAD Total & Retour BL",
    "version": "19.0.1.0.0",
    "summary": "Adds MAD total field and Retour sur BL on credit notes",
    "category": "Accounting",
    "author": "Schiele",
    "license": "LGPL-3",
    "depends": ["account", "sh_invoice_picking"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
}
