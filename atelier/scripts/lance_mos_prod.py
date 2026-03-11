#!/usr/bin/env python3
"""
Script Odoo Shell – Lancer les OFs WH/MO en cours dans l'atelier
-----------------------------------------------------------------
Usage (sur le serveur de prod) :
    cd /path/to/odoo
    python odoo-bin shell -c /path/to/odoo.conf -d <nom_base> < /tmp/lance_mos_prod.py

Ce script :
  1. Affiche un aperçu de tous les OFs concernés AVANT toute modification.
  2. Attend votre confirmation (Y) avant d'appliquer.
  3. Pour chaque OF trouvé :
     - Passe is_lancer = True
     - Ajoute les employés de employee_assigned_ids dans atelier_worker_ids
"""

# ── Recherche ──────────────────────────────────────────────────
productions = env['mrp.production'].search([
    ('name', 'like', 'WH/MO%'),
    ('state', '=', 'progress'),
    ('employee_assigned_ids', '!=', False),
])

if not productions:
    print("⚠  Aucun OF trouvé correspondant aux critères.")
    exit()

# ── Aperçu ─────────────────────────────────────────────────────
print("\n" + "="*70)
print(f"  {len(productions)} OF(s) vont être lancés dans l'atelier :")
print("="*70)
for mo in productions:
    emp_names = ', '.join(mo.employee_assigned_ids.mapped('name'))
    already_workers = ', '.join(mo.atelier_worker_ids.mapped('name')) if mo.atelier_worker_ids else '—'
    already_lancer  = '✔' if mo.is_lancer else '✘'
    print(f"\n  [{mo.name}]  état={mo.state}  is_lancer={already_lancer}")
    print(f"    employee_assigned_ids : {emp_names}")
    print(f"    atelier_worker_ids    : {already_workers}")
print("\n" + "="*70)

# ── Confirmation ────────────────────────────────────────────────
answer = input("\nAppliquer ces modifications ? (Y/n) : ").strip().lower()
if answer not in ('y', 'yes', ''):
    print("❌ Annulé – aucune modification effectuée.")
    exit()

# ── Application ─────────────────────────────────────────────────
updated = 0
for mo in productions:
    new_emp_ids = mo.employee_assigned_ids.ids
    mo.write({
        'is_lancer': True,
        'atelier_worker_ids': [(4, eid) for eid in new_emp_ids],
    })
    updated += 1
    print(f"  ✔ {mo.name} → lancé | workers: {', '.join(mo.employee_assigned_ids.mapped('name'))}")

env.cr.commit()
print(f"\n✅ {updated} OF(s) mis à jour et commités en base.")
