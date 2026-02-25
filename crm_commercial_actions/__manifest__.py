{
    "name": "CRM Commercial Actions",
    "version": "19.0.1.1.0",
    "author": "Mouad Lyaazale",
    "price": 20.99,
    "currency": "EUR",
    "category": "Sales/CRM",
    "summary": "Adds configurable Actions Commerciales table to Opportunities",
    "depends": ["crm"],
    "data": [
        "security/ir.model.access.csv",
        "views/crm_action_template_views.xml",
        "views/crm_lead_views.xml",
    ],
    "installable": True,
    "application": False,
}
