{
    "name": "Statut de facturation BL (Softhealer + Odoo)",
    "version": "19.0.6.0.0",
    "category": "Inventory",
    "summary": "Statut de facturation sur les bons de livraison (Facturé / Prêt / Non prêt) - basé sur quantités facturées vs livrées",
    "depends": ["stock", "sale_management", "account"],
    "data": [
        "views/stock_picking_views.xml"
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3"
}
