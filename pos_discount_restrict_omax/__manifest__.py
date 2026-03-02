# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'POS Discount Restrict',
    'version' : '19.0.1.0',
    'category': 'Point of Sale,Human Resources',
    'sequence': 1,
    'author': 'OMAX Informatics',
    'website': 'https://www.omaxinformatics.com',
    'description': '''The POS Discount Restrict module controls discount permissions in Odoo POS by setting per-employee discount limits, requiring PIN approval for higher discounts, and allowing authorized employees to override restrictions.''',
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
            'pos_discount_restrict_omax/static/src/js/discount_popup.js',
            'pos_discount_restrict_omax/static/src/xml/discount_popup.xml',
            'pos_discount_restrict_omax/static/src/js/orderline.js',
            'pos_discount_restrict_omax/static/src/js/price_limit.js',
        ]
    },
    'demo': [],
    'test': [],
     'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'currency':'USD',
    'price': 25.0,
    'installable': True,
    'auto_install' : False,
    'application': True,
    'pre_init_hook': 'pre_init_check',
    'module_type': 'official',
    'summary': '''The POS Discount Restrict module enhances Odoo POS by enforcing employee-level discount permissions with PIN verification. It ensures only authorized staff can override discount limits, improving security, control, and accountability.
    Control and restrict discounts in Odoo POS with employee-level permissions. Set maximum discount limits, require PIN approval for overrides, and allow only authorized staff to apply unrestricted discounts.
    pos discount restrict pos discount control  pos discount approval  pos restrict discount  pos discount permission  pos discount security  pos employee discount control  pos employee pin approval  pos pin code discount  pos cashier discount approval  pos restrict by employee  pos discount limit  pos maximum discount  pos override discount  pos discount settings  pos manager approval
    ''',
}
