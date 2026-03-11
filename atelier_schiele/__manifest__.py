{
    'name': 'Atelier',
    'version': '19.0.1.0.0',
    'summary': 'Shop-floor kiosk with PIN login, real-time time tracking & supervisor dashboard for manufacturing orders',
    'description': """
=======
Atelier
=======

A dedicated shop-floor kiosk and supervisor dashboard for Odoo Manufacturing.

Key Features
------------
* **Touchscreen kiosk** accessible at /atelier — no Odoo login required for technicians.
* **PIN / badge login** — each technician authenticates with a personal PIN.
* **Real-time time tracking** — Start, Pause, and Stop timers per work-order operation;
  blocks are stored in ``mrp.workcenter.productivity`` (same as native Shop Floor).
* **Shift (vacation) management** — define shifts with automatic timer auto-close at shift end.
* **Supervisor dashboard** at /atelier/supervisor — live activity, launched MOs, daily
  technician summary, shift view and performance statistics.
* **Priority & burndown** — mark MOs as Normal / Urgent / Critical and track
  time-consumed percentage across all operations.
* **Auto-quality check** — autocontrôle quality check created automatically when an MO
  is launched to the kiosk.
* **Pointage report** — printable daily time-sheet per technician.
    """,
    'category': 'Manufacturing',
    'author': 'mouad lyaazale',
    'price': 300.0,
    'currency': 'USD',
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
