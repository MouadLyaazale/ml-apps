# -*- coding: utf-8 -*-
"""
Wizard : Créer la facture fournisseur (in_invoice) de débours
=============================================================
Perspective CLIENT – nous recevons une facture du prestataire (transitaire…)
qui a avancé des frais pour notre compte.

Écriture générée par Odoo lors de la validation de la facture fournisseur :
  Dr 6114xx  Charges débours (frais avancés)                 HORS TVA
  Dr 614250  Honoraires prestataire HT
  Dr 345520  TVA récupérable 20% (sur encaissement si régime encaissement)
     Cr 4411  Fournisseurs
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DeboursFacturationWizard(models.TransientModel):
    _name = 'debours.facturation.wizard'
    _description = "Wizard – Création Facture Fournisseur Débours"

    dossier_id = fields.Many2one(
        'debours.dossier',
        string='Dossier',
        required=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        related='dossier_id.partner_id',
        readonly=True,
        string='Prestataire',
    )
    date_facture = fields.Date(
        string='Date Facture',
        default=fields.Date.today,
        required=True,
    )
    date_echeance = fields.Date(
        string="Date d'Échéance",
        required=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        string="Journal d'Achats",
        domain="[('type', '=', 'purchase')]",
        required=True,
    )
    ref_facture = fields.Char(
        string='Réf. Facture Prestataire',
        help="Numéro de la facture envoyée par le transitaire/notaire",
    )
    # Résumé lecture seule
    total_debours = fields.Monetary(
        related='dossier_id.total_debours',
        currency_field='currency_id',
        readonly=True,
        string='Total Débours (HORS TVA)',
    )
    honoraires_ht = fields.Monetary(
        related='dossier_id.honoraires_ht',
        currency_field='currency_id',
        readonly=True,
    )
    tva_honoraires = fields.Monetary(
        related='dossier_id.tva_honoraires',
        currency_field='currency_id',
        readonly=True,
        string='TVA Récupérable',
    )
    montant_total = fields.Monetary(
        related='dossier_id.montant_facture_fournisseur',
        currency_field='currency_id',
        readonly=True,
        string='Total Facture Fournisseur',
    )
    currency_id = fields.Many2one(
        related='dossier_id.currency_id',
        readonly=True,
    )
    regime_encaissement = fields.Boolean(
        related='dossier_id.regime_encaissement',
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        dossier_id = self.env.context.get('default_dossier_id')
        if dossier_id:
            dossier = self.env['debours.dossier'].browse(dossier_id)
            config = self.env['debours.config'].search([
                ('company_id', '=', dossier.company_id.id)
            ], limit=1)
            if config and config.journal_achat_id:
                res['journal_id'] = config.journal_achat_id.id
            from datetime import timedelta
            import datetime
            today = datetime.date.today()
            res['date_facture'] = today
            res['date_echeance'] = today + timedelta(days=30)
        return res

    def action_create_bill(self):
        self.ensure_one()
        dossier = self.dossier_id

        if dossier.state != 'validated':
            raise UserError(_("Le dossier doit être à l'état 'Validé' pour créer la facture fournisseur."))

        config = self.env['debours.config'].search([
            ('company_id', '=', dossier.company_id.id)
        ], limit=1)

        account_debours = config and config.account_debours_id
        account_honoraires = config and config.account_honoraires_id

        if not account_debours and dossier.line_ids:
            raise UserError(_(
                "Configurez le compte de charges débours dans\n"
                "Comptabilité > Débours > Configuration."
            ))
        if dossier.honoraires_ht and not account_honoraires:
            raise UserError(_(
                "Configurez le compte honoraires prestataire dans\n"
                "Comptabilité > Débours > Configuration."
            ))

        # ── Construction des lignes de facture fournisseur ──────────────────
        invoice_lines = []

        # Ligne(s) débours – HORS TVA (frais pour ordre, pas de TVA récupérable)
        for line in dossier.line_ids:
            invoice_lines.append((0, 0, {
                'name': line.name,
                'account_id': account_debours.id,
                'price_unit': line.montant,
                'quantity': 1.0,
                'tax_ids': [],   # Débours : HORS TVA
            }))

        # Ligne honoraires prestataire HT – avec TVA récupérable
        if dossier.honoraires_ht and account_honoraires:
            tax_ids = []
            if dossier.taux_tva:
                base_domain = [
                    ('type_tax_use', '=', 'purchase'),
                    ('amount', '=', dossier.taux_tva),
                    ('amount_type', '=', 'percent'),
                    ('company_id', '=', dossier.company_id.id),
                ]
                if dossier.regime_encaissement:
                    # Cherche taxe achat on_payment (TVA récup. = à notre paiement)
                    tax = self.env['account.tax'].search(
                        base_domain + [('tax_exigibility', '=', 'on_payment')],
                        limit=1,
                    )
                    if not tax:
                        tax = self.env['account.tax'].search(base_domain, limit=1)
                else:
                    tax = self.env['account.tax'].search(base_domain, limit=1)
                if tax:
                    tax_ids = [(4, tax.id)]

            invoice_lines.append((0, 0, {
                'name': _('Honoraires – %s') % dossier.name,
                'account_id': account_honoraires.id,
                'price_unit': dossier.honoraires_ht,
                'quantity': 1.0,
                'tax_ids': tax_ids,
            }))

        bill_vals = {
            'move_type': 'in_invoice',
            'partner_id': dossier.partner_id.id,
            'journal_id': self.journal_id.id,
            'invoice_date': self.date_facture,
            'invoice_date_due': self.date_echeance,
            'company_id': dossier.company_id.id,
            'ref': self.ref_facture or (_('Débours – %s') % dossier.name),
            'narration': (
                _("Régime encaissement – TVA récupérable à notre paiement (art. 10 CGI Maroc)")
                if dossier.regime_encaissement
                else ''
            ),
            'invoice_line_ids': invoice_lines,
        }

        bill = self.env['account.move'].create(bill_vals)
        dossier.vendor_bill_ids = [(4, bill.id)]

        # Marquer toutes les lignes comme incluses
        dossier.line_ids.write({'state': 'included'})

        # Passer le dossier à "billed"
        dossier.state = 'billed'
        dossier.message_post(body=_(
            "Facture fournisseur créée : %s – Total : %.2f MAD"
        ) % (bill.name or _('Brouillon'), dossier.montant_facture_fournisseur))

        # Ouvrir la facture fournisseur
        return {
            'type': 'ir.actions.act_window',
            'name': _('Facture Fournisseur – Débours'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': bill.id,
        }
