# -*- coding: utf-8 -*-
"""
debours.config  – Configuration comptable des débours par société
Perspective CLIENT : comptes de charges + TVA récupérable + fournisseurs
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DebourConfig(models.Model):
    _name = 'debours.config'
    _description = 'Configuration Débours Marocain'

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company,
    )
    # Compte de charges pour les débours (frais avanc és par le prestataire)
    account_debours_id = fields.Many2one(
        'account.account',
        string='Compte Charges Débours',
        help="Compte de charge pour les frais débours (HORS TVA) – ex: 61110010 Achats import/transitaire",
    )
    # Compte de charges pour les honoraires du prestataire
    account_honoraires_id = fields.Many2one(
        'account.account',
        string='Compte Honoraires Prestataire',
        help="Compte de charge pour les honoraires du transitaire/notaire – ex: 614250",
    )
    # Compte TVA récupérable sur charges
    account_tva_id = fields.Many2one(
        'account.account',
        string='Compte TVA Récupérable',
        help="Compte TVA récupérable sur charges – ex: 345520",
    )
    # Journal d'achats par défaut
    journal_achat_id = fields.Many2one(
        'account.journal',
        string="Journal d'Achats",
        domain="[('type', '=', 'purchase')]",
    )

    @api.constrains('company_id')
    def _check_company_unique(self):
        for rec in self:
            if self.search_count([('company_id', '=', rec.company_id.id)]) > 1:
                raise ValidationError(
                    _('Une seule configuration de débours par société est permise.')
                )
