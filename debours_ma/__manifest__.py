# -*- coding: utf-8 -*-
{
    'name': 'Gestion des Débours Marocains',
    'version': '19.0.2.0.0',
    'price': 149.0,
    'category': 'Accounting/Accounting',
    'summary': "Debours Maroc / Supplier Bill: TVA encaissement, transitaire, suivi dossier",
    'description': """
Gestion des Débours Marocains (Odoo 19)
=======================================

Le module couvre le flux CLIENT de débours au Maroc: lorsqu'un prestataire
(transitaire, notaire, avocat, courtier...) avance des frais pour votre compte,
vous centralisez le dossier, générez la facture fournisseur et suivez le paiement
dans un processus propre et conforme au régime d'encaissement.

Fonctionnalites principales
---------------------------
- Dossier de débours avec reference automatique et suivi d'etat
- Lignes de débours detaillees (tiers paye, piece justificative, montant)
- Gestion des honoraires prestataire avec TVA paramétrable
- Wizard de creation de facture fournisseur depuis le dossier
- Integration native avec la comptabilite Odoo (account.move)
- Smart buttons pour accéder aux factures fournisseur liees
- Historique et suivi via chatter (mail.thread)

Flux metier couvert
-------------------
1. Creation du dossier de débours (lignes + honoraires)
2. Validation du dossier
3. Generation de la facture fournisseur en un clic
4. Paiement de la facture via le flux standard Odoo
5. Passage du dossier a l'etat paye avec traçabilite complete

Comptabilisation ciblee (Maroc)
-------------------------------
- Débours: charges hors TVA
- Honoraires: HT + TVA recuperable
- Regime d'encaissement: TVA deductible a votre paiement

Benefices
---------
- Gagnez du temps dans la gestion quotidienne des dossiers de débours
- Reduisez les erreurs de saisie et de ventilation comptable
- Standardisez un flux metier clair entre achats, finance et comptabilite
- Ameliorez la visibilite sur les montants avances et payes

Support et personnalisation
---------------------------
Le module est pret pour la production et peut etre adapte a votre plan de comptes,
vos journaux et vos regles internes.

English quick description
-------------------------
Debours Maroc helps Moroccan companies manage provider disbursements end-to-end:
disbursement file, supplier bill generation, payment tracking, and deductible VAT
under cash basis rules. Typical use cases include freight forwarder (transitaire),
notary, and broker advanced expenses.
    """,
    'author': 'Mouad Lyaazale',
    'website': 'https://www.odoo.com',
    'support': 'mouad.lyaazale@gmail.com',
    'images': ['static/description/banner.png'],
    'depends': ['account', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'data/debours_sequence.xml',
        'data/debours_account_data.xml',
        'views/debours_dossier_views.xml',
        'views/debours_line_views.xml',
        'views/debours_invoice_views.xml',
        'views/debours_menu.xml',
        'wizard/debours_paiement_wizard_views.xml',
        'wizard/debours_facturation_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
