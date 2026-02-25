# -*- coding: utf-8 -*-
{
    'name': "Fix Stock Return Access Rights",
    'summary': "Allows users to create returns even if they don't have write access to product variants",
    'description': """
        This module overrides the stock return process to run with elevated privileges (sudo).
        This fixes the issue where creating a return triggers a write on product.product (e.g. for tracking fields),
        but the user does not have permission to modify products.
    """,
    'category': 'Inventory',
    'version': '19.0.0.1',
    'depends': ['stock'],
    'data': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
