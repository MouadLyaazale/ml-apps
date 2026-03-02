{
    'name': 'Bank Matching - Force Tax Declaration',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Add button to force VAT declaration from bank reconciliation interface',
    'description': """
    This module adds a button in the bank reconciliation interface (Tableau de bord)
    to force VAT declaration directly from bank matching lines.
    
    When an account code 345520 (État - TVA récupérable sur les charges) is detected,
    a button appears to immediately force the tax declaration in the VAT report.
    """,
    'author': 'Schiele',
    'depends': [
        'account',
        'account_effet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_line_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'auto_install': False,
}
