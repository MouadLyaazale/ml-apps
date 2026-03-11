import os

_path = os.path.dirname(__file__)
_description_file = os.path.join(_path, 'static', 'description', 'index.html')
_description_html = ''
if os.path.exists(_description_file):
    with open(_description_file, 'r', encoding='utf-8') as f:
        _description_html = f.read()

{
    'name': 'Atelier',
    'version': '19.0.1.0.0',
    'summary': 'Shop-floor kiosk with PIN login, real-time time tracking & supervisor dashboard for manufacturing orders',
    'description': _description_html or "Atelier shop-floor kiosk for Odoo Manufacturing.",
    'category': 'Manufacturing',
    'author': 'mouad lyaazale',
    'price': 300.0,
    'currency': 'USD',
    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
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