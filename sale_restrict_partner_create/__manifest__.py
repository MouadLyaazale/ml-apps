# -*- coding: utf-8 -*-
{
    'name': "Restrict Partner Quick Create in Sales",
    'summary': "Disables quick create and create & edit for customers in Quotes and Sale Orders",
    'description': """
        This module removes the "Create" and "Create and Edit" options from the customer field
        in Quotations and Sale Orders.
    """,
    'category': 'Sales',
    'version': '19.0.0.1',
    'depends': ['sale'],
    'data': [
        'views/sale_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
