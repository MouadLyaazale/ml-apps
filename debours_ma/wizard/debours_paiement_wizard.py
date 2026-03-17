# -*- coding: utf-8 -*-
"""
debours.paiement.wizard – conservé pour compatibilité avec la base de données.
En tant que CLIENT, le paiement des factures fournisseurs se fait via le
mécanisme standard d'Odoo (Enregistrer un Paiement sur la facture fournisseur).
Ce wizard n'est plus utilisé dans le flux principal.
"""

from odoo import fields, models


class DeboursPaiementWizard(models.TransientModel):
    _name = 'debours.paiement.wizard'
    _description = 'Wizard Paiement Débours (obsolète – voir facture fournisseur)'

    dossier_id = fields.Many2one('debours.dossier', string='Dossier', readonly=True)
