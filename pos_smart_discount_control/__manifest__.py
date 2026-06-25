# -*- coding: utf-8 -*-
# © 2025 Mouad Lyaazale. All rights reserved.
{
    'name': 'POS Pro Suite — Discount, Stock & Delivery',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'sequence': 1,
    'author': 'Mouad Lyaazale',
    'maintainer': 'Mouad Lyaazale',
    'support': 'mouad.lyaazale@gmail.com',
    'description': '''
POS Smart Discount Control
===========================

Take full control of discounts and pricing in your Odoo Point of Sale.

1. **Discount Limit with PIN Approval**
   Prevent cashiers from applying discounts above a configured threshold.
   A manager or authorized employee must validate with their PIN.

2. **Minimum Price Guard**
   Block payment if the effective price after discount falls below a
   configured floor percentage. Requires PIN override from authorized staff.

3. **Real-time Stock Badge on Products**
   Display the free-to-sell quantity (on-hand minus reserved) directly on
   each product card inside POS.  Color-coded: Red = 0, Orange = 1–5, Green > 5.

4. **Block Receipt Until Transfer is Validated**
   After payment, the receipt screen is locked and invoice creation is blocked
   until the linked stock delivery is fully validated.

5. **Reprint Delivery Slip (A4) from POS**
   One-click button on the receipt screen to open the A4 delivery slip
   (via configured DOCX template) in a new browser tab.

6. **Force-Edit Posted Order Payments**
   A backend wizard lets managers correct or reassign payment lines on
   already-posted POS orders without cancelling the entire session.
''',
    'depends': ['point_of_sale','hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee.xml',
        'views/res_config_setting.xml',
        'views/pos_order_views.xml',
        'wizard/wizard_views.xml',
    ],
    'assets':{
        'point_of_sale._assets_pos':[
            'pos_smart_discount_control/static/src/js/discount_popup.js',
            'pos_smart_discount_control/static/src/xml/discount_popup.xml',
            'pos_smart_discount_control/static/src/js/orderline.js',
            'pos_smart_discount_control/static/src/js/price_limit.js',
            'pos_smart_discount_control/static/src/js/product_stock.js',
            'pos_smart_discount_control/static/src/js/picking_block.js',
            'pos_smart_discount_control/static/src/js/receipt_bl_a4.js',
            'pos_smart_discount_control/static/src/xml/receipt_bl_a4.xml',
            'pos_smart_discount_control/static/src/xml/product_stock.xml',
        ]
    },
    'demo': [],
    'test': [],
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'currency': 'USD',
    'installable': True,
    'auto_install': False,
    'application': True,
    'pre_init_hook': 'pre_init_check',
    'summary': (
        'All-in-one POS operations suite: PIN-protected discount limits, minimum price guard, '
        'live stock quantity badges on product cards, receipt blocked until delivery validated, '
        'A4 delivery slip printing, and post-order payment editor. '
        'pos discount restrict | pos discount limit | pos pin approval | pos cashier control | '
        'pos minimum price | pos stock badge | pos delivery slip | pos bl print | pos stock card'
    ),
}
