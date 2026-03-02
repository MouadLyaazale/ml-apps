{
    'name': "Fix Invoice Price Readonly",
    'summary': "Removes the readonly restriction on invoice line price when reference is set",
    'description': """
        This module overrides the behavior introduced by account_effet where the unit price
        becomes readonly if the invoice reference is set.
    """,
    'author': "GitHub Copilot",
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['account', 'account_effet'],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
