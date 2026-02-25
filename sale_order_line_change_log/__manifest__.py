{
    'name': 'Sale Order Line Change Log',
    'version': '17.0.1.0.0',
    'summary': 'Track and log all changes made to sale order lines',
    'description': """
Sale Order Line Change Log
==========================

This module tracks and logs all changes made to sale order lines.

Features:
---------
- Automatically records every modification to sale order lines
- Tracks changes to: product, quantity, unit price, discount, and description
- Logs the user who made the change and the date/time of the change
- Stores both old and new values for every field change
- View the full change history directly from the sale order line
- Filter and search change logs by date, user, or field name

How it works:
-------------
Whenever a sale order line is modified, the module automatically creates
a change log entry capturing the field that was changed, the previous value,
the new value, the user who made the change, and the timestamp.

Use Cases:
----------
- Audit trail for sale order modifications
- Track pricing changes and who approved them
- Monitor quantity adjustments over time
- Compliance and accountability tracking
    """,
    'category': 'Sales/Sales',
    'author': 'MouadLyaazale',
    'license': 'GPL-3',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_line_log_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
