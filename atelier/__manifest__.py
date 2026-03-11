{
    'name': 'Atelier',
    'version': '19.0.1.0.0',
    'summary': 'Shop-floor kiosk with PIN login, real-time time tracking & supervisor dashboard for manufacturing orders',
    'description': """
Atelier shop-floor kiosk for Odoo Manufacturing.
    """,
    'category': 'Manufacturing',
    'author': 'mouad lyaazale',
    'price': 300.0,
    'currency': 'USD',
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
        'static/description/config pin employee form.png',
        'static/description/entree atelier kiosk.png',
        'static/description/kiosk in order de fabrication menu.png',
        'static/description/menu block de temps.png',
        'static/description/menu of lancer.png',
        'static/description/menu superviseur.png',
        'static/description/menu tecnician.png',
        'static/description/menu vacation.png',
        'static/description/of lancer superviseur menu.png',


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
    'assets': {'atelier._assets_atelier':[
            'atelier/static/src/js/atelier_app.js',
            'atelier/static/src/js/supervisor_app.js',
            'atelier/static/src/css/atelier.css',
            'atelier/static/src/css/supervisor.css',

        ]},
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
