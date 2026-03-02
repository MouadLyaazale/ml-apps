# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
{
    "name": "Warehouse Restriction for User | Stock Location Restriction",
    "version": "19.0.0.2",
    "category": "Warehouse",
    "summary": "warehouse user restriction User Warehouse Restriction Warehouse location restriction user restriction on warehouse location stock access control stock restriction restrict warehouse restrict stock operation restriction stock access warehouse access rules",
    "description": """ 

        Warehouse Restriction for User in odoo,
        Configure Restriction in odoo,
        Operation Types Restriction in odoo,
        Warehouse Locations Restriction in odoo,
        Warehouse Restriction in odoo,

    """,
    "author": "BROWSEINFO",
    "price": 23,
    "currency": "EUR",
    "website": "https://www.browseinfo.com/demo-request?app=bi_warehouse_restrictions&version=18&edition=Community",
    "depends": ["base", "stock"],
    "data": [
        "security/restriction_rules.xml",
        "views/res_users_inherited.xml",
    ],
    "license": "OPL-1",
    "installable": True,
    "auto_install": False,
    "live_test_url": "https://www.browseinfo.com/demo-request?app=bi_warehouse_restrictions&version=18&edition=Community",
    "images": ["static/description/Banner.gif"],
}
