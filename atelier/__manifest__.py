{
    'name': 'Atelier',
    'version': '19.0.1.0.0',
    'summary': 'Shop-floor kiosk with PIN login, real-time time tracking & supervisor dashboard for manufacturing orders',
    'description': """
Atelier shop-floor kiosk for Odoo Manufacturing.
See static/Description/index.html for the full Apps Store description.
    """,
    'category': 'Manufacturing',
    'author': 'mouad lyaazale',
    'price': 300.0,
    'currency': 'USD',
    'images': [
        'static/Description/banner.png',
        'static/Description/icon.png',
        'static/Description/config pin employee form.png',
        'static/Description/entree atelier kiosk',
        'static/Description/kiosk in order de fabrication menu.png',
        'static/Description/menu block de temps.png',
        'static/Description/menu of lancer.png',
        'static/Description/menu superviseur.png',
        'static/Description/menu tecnician.png',
        'static/Description/menu vacation.png',
        'static/Description/of lancer superviseur menu.png',


    ],
    'depends': ['mrp', 'hr', 'web', 'quality_control', 'quality_mrp_workorder'],
    'data': [
        'security/ir.model.access.csv',
        'data/atelier_params.xml',
        'data/atelier_cron.xml',
        'views/atelier_shift_views.xml',
        'views/atelier_wizard_views.xml',
        'views/atelier_production_views.xml',
        'views/atelier_employee_views.xml',
        'views/atelier_kiosk_page.xml',
        'views/atelier_supervisor_page.xml',
        'views/atelier_menus.xml',
        'reports/atelier_pointage_report.xml',
    ],
    'assets': {},
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
