# -*- coding: utf-8 -*-
"""
debours.line  – Ligne de débours (un frais avancé par le prestataire pour notre compte)
========================================================================================
Perspective CLIENT : le prestataire (transitaire, notaire…) a AVANCÉ ces frais
pour notre compte. Ces montants seront repris SANS TVA sur la facture fournisseur.
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DebourLine(models.Model):
    _name = 'debours.line'
    _description = 'Ligne de Débours'
    _order = 'dossier_id, date_depense'

    dossier_id = fields.Many2one(
        'debours.dossier',
        string='Dossier',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(
        string='Libellé',
        required=True,
        help="Description du frais avancé (ex: Droits de douane, Frais de transit…)",
    )
    date_depense = fields.Date(
        string='Date',
        default=fields.Date.today,
        required=True,
    )

    # Tiers auquel le prestataire a payé ce frais
    partner_tiers_id = fields.Many2one(
        'res.partner',
        string='Payé À',
        help="Administration, organisme ou fournisseur à qui ce frais a été versé (ex: Douane, Port)",
    )

    # Montant
    montant = fields.Monetary(
        string='Montant (MAD)',
        currency_field='currency_id',
        required=True,
    )
    currency_id = fields.Many2one(
        related='dossier_id.currency_id',
        readonly=True,
    )

    # Pièce justificative
    ref_piece = fields.Char(
        string='Réf. Pièce',
        help="N° de reçu, bordereau douane, quittance…",
    )

    state = fields.Selection([
        ('draft', 'À Facturer'),
        ('included', 'Inclus en Facture'),
    ], string='État', default='draft', readonly=True)

    notes = fields.Text(string='Notes')
