# -*- coding: utf-8 -*-
"""
debours.dossier  – Dossier de débours marocain (Perspective CLIENT)
====================================================================
Nous sommes le CLIENT qui reçoit des services de prestataires
(transitaires, notaires, avocats, courtiers…) lesquels ont avancé
des frais pour notre compte.

Cycle :
  1. draft      → Brouillon : saisie des lignes de débours + honoraires
  2. validated  → Dossier validé, prêt pour la facturation fournisseur
  3. billed     → Facture fournisseur (in_invoice) créée dans Odoo
  4. paid       → Facture fournisseur payée – TVA 3455 récupérée
  5. cancel     → Annulé

Écritures générées par Odoo lors de la validation de la facture fournisseur :
  Dr 6114xx  Charges débours (frais avancés par le prestataire)   HORS TVA
  Dr 614250  Honoraires prestataire HT
  Dr 345520  TVA récupérable 20%  (exigible à notre paiement si régime enc.)
     Cr 4411  Fournisseurs
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class DeboursDossier(models.Model):
    _name = 'debours.dossier'
    _description = 'Dossier de Débours Marocain'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_dossier desc, name desc'

    # ─── Identification ────────────────────────────────────────────────────────
    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau'),
        tracking=True,
    )
    description = fields.Text(string='Description / Opération')
    date_dossier = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )

    # ─── Prestataire (transitaire, notaire, courtier…) ─────────────────────────
    partner_id = fields.Many2one(
        'res.partner',
        string='Prestataire / Transitaire',
        required=True,
        tracking=True,
        help="Fournisseur qui a avancé les frais pour notre compte (transitaire, notaire, etc.)",
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        readonly=True,
    )

    # ─── Régime TVA ────────────────────────────────────────────────────────────
    regime_encaissement = fields.Boolean(
        string='Fournisseur en Régime Encaissement',
        default=True,
        tracking=True,
        help="Si coché, le prestataire est soumis au régime d'encaissement.\n"
             "La TVA (3455) sur ses honoraires n'est récupérable qu'après notre paiement.\n"
             "Les débours eux-mêmes sont toujours HORS TVA (frais pour ordre).",
    )

    # ─── Honoraires du prestataire ─────────────────────────────────────────────
    honoraires_ht = fields.Monetary(
        string='Honoraires Prestataire HT',
        currency_field='currency_id',
        default=0.0,
        tracking=True,
        help="Rémunération du prestataire (hors débours), soumise à TVA",
    )
    taux_tva = fields.Float(
        string='Taux TVA (%)',
        default=20.0,
        help="Taux TVA applicable aux honoraires du prestataire (défaut Maroc : 20%)",
    )
    tva_honoraires = fields.Monetary(
        string='TVA Récupérable',
        compute='_compute_tva',
        store=True,
        currency_field='currency_id',
        help="TVA 20% sur honoraires – récupérable (compte 3455)",
    )
    honoraires_ttc = fields.Monetary(
        string='Honoraires TTC',
        compute='_compute_tva',
        store=True,
        currency_field='currency_id',
    )

    # ─── Lignes de débours ─────────────────────────────────────────────────────
    line_ids = fields.One2many(
        'debours.line',
        'dossier_id',
        string='Débours (Frais Avancés par le Prestataire)',
    )
    total_debours = fields.Monetary(
        string='Total Débours',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help="Somme des frais avancés par le prestataire pour notre compte (HORS TVA)",
    )

    # ─── Montant total de la facture fournisseur ───────────────────────────────
    montant_facture_fournisseur = fields.Monetary(
        string='Total Facture Fournisseur',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help="Débours (HT) + Honoraires HT + TVA = Total à payer au prestataire",
    )

    # ─── Liens factures fournisseur ────────────────────────────────────────────
    vendor_bill_ids = fields.Many2many(
        'account.move',
        'debours_dossier_bill_rel',
        'dossier_id',
        'move_id',
        string='Factures Fournisseur',
        domain="[('move_type', '=', 'in_invoice')]",
        readonly=True,
    )
    vendor_bill_count = fields.Integer(compute='_compute_counts')

    # ─── Statut ────────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
        ('billed', 'Facturé Fournisseur'),
        ('paid', 'Payé'),
        ('cancel', 'Annulé'),
    ], string='État', default='draft', tracking=True, copy=False)

    # ──────────────────────────────────────────────────────────────────────────
    # Computes
    # ──────────────────────────────────────────────────────────────────────────

    @api.depends('honoraires_ht', 'taux_tva')
    def _compute_tva(self):
        for rec in self:
            tva = rec.honoraires_ht * (rec.taux_tva / 100.0)
            rec.tva_honoraires = tva
            rec.honoraires_ttc = rec.honoraires_ht + tva

    @api.depends('line_ids.montant', 'honoraires_ttc')
    def _compute_totals(self):
        for rec in self:
            rec.total_debours = sum(rec.line_ids.mapped('montant'))
            rec.montant_facture_fournisseur = rec.total_debours + rec.honoraires_ttc

    @api.depends('vendor_bill_ids')
    def _compute_counts(self):
        for rec in self:
            rec.vendor_bill_count = len(rec.vendor_bill_ids)

    # ──────────────────────────────────────────────────────────────────────────
    # ORM
    # ──────────────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', _('Nouveau')) == _('Nouveau'):
                vals['name'] = seq.next_by_code('debours.dossier') or _('Nouveau')
        return super().create(vals_list)

    # ──────────────────────────────────────────────────────────────────────────
    # Actions boutons
    # ──────────────────────────────────────────────────────────────────────────

    def action_validate(self):
        """Valide le dossier : vérifie qu'il y a au moins une ligne."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Ce dossier n'est pas en brouillon."))
            if not rec.line_ids and not rec.honoraires_ht:
                raise UserError(_(
                    "Ajoutez au moins une ligne de débours ou un montant d'honoraires."
                ))
            rec.state = 'validated'
            rec.message_post(body=_("Dossier validé – prêt pour la création de la facture fournisseur."))

    def action_mark_paid(self):
        """Passe à 'Payé' – vérifie que la facture fournisseur est bien payée dans Odoo.

        En régime d'encaissement (du côté fournisseur) : la TVA 3455 récupérable
        n'est déduite que lorsque nous payons le prestataire. Odoo gère cela
        automatiquement via la taxe avec tax_exigibility='on_payment'.
        """
        for rec in self:
            if rec.state != 'billed':
                raise UserError(_("Le dossier doit être à l'état 'Facturé Fournisseur' pour être payé."))
            unpaid_bills = rec.vendor_bill_ids.filtered(
                lambda b: b.payment_state not in ('paid', 'in_payment', 'reversed')
            )
            if unpaid_bills:
                raise UserError(_(
                    "La facture fournisseur n'est pas encore payée dans Odoo.\n"
                    "Enregistrez le paiement sur la facture fournisseur, puis "
                    "revenez marquer le dossier comme payé."
                ))
            rec.state = 'paid'
            if rec.regime_encaissement:
                rec.message_post(body=_(
                    "Paiement enregistré. TVA récupérable de %(tva)s MAD (compte 3455) "
                    "désormais déduite (régime encaissement fournisseur)."
                ) % {'tva': rec.tva_honoraires})
            else:
                rec.message_post(body=_("Dossier payé."))

    def action_cancel(self):
        for rec in self:
            if rec.state in ('paid',):
                raise UserError(_("Un dossier payé ne peut pas être annulé."))
            rec.state = 'cancel'
            rec.message_post(body=_("Dossier annulé."))

    def action_reset_draft(self):
        for rec in self:
            if rec.state not in ('cancel',):
                raise UserError(_("Seul un dossier annulé peut être remis en brouillon."))
            rec.state = 'draft'

    # ──────────────────────────────────────────────────────────────────────────
    # Smart buttons
    # ──────────────────────────────────────────────────────────────────────────

    def action_view_vendor_bills(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Factures Fournisseur'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.vendor_bill_ids.ids)],
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Wizard launchers
    # ──────────────────────────────────────────────────────────────────────────

    def action_open_bill_wizard(self):
        """Ouvre le wizard pour créer la facture fournisseur (in_invoice)."""
        if self.state not in ('validated',):
            raise UserError(_("Validez d'abord le dossier avant de créer la facture fournisseur."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Créer Facture Fournisseur (Débours)'),
            'res_model': 'debours.facturation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_dossier_id': self.id},
        }
