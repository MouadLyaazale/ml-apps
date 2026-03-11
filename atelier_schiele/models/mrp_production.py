from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    atelier_priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Urgent'),
        ('2', 'Critique'),
    ], string='Priorité atelier', default='0', tracking=True)

    atelier_burndown = fields.Float(
        string='Burndown (%)',
        compute='_compute_atelier_burndown',
        store=False,
        help='Pourcentage du temps prévu déjà consommé (toutes opérations)',
    )

    @api.depends('workorder_ids.duration', 'workorder_ids.duration_expected')
    def _compute_atelier_burndown(self):
        for prod in self:
            total_expected = sum(prod.workorder_ids.mapped('duration_expected')) or 0
            total_done     = sum(prod.workorder_ids.mapped('duration')) or 0
            prod.atelier_burndown = round(
                (total_done / total_expected * 100) if total_expected else 0.0, 1
            )

    is_lancer = fields.Boolean(
        string='Lancé',
        default=False,
        tracking=True,
        help="Cocher pour rendre cet OF visible dans le kiosque atelier.",
    )
    atelier_worker_ids = fields.Many2many(
        'hr.employee',
        'atelier_production_worker_rel',
        'production_id',
        'employee_id',
        string='Techniciens assignés',
        help="Seuls ces techniciens verront cet OF dans le kiosque.",
    )

    def action_lancer(self):
        """Marque l'OF comme 'Lancé' — le rend visible dans le kiosque."""
        for rec in self:
            if rec.state not in ('confirmed', 'progress', 'to_close'):
                raise ValidationError(
                    _("Seuls les OF confirmés ou en cours peuvent être lancés.")
                )
            rec.is_lancer = True
            # ── Feature C : créer un check Autocontrôle pour chaque opération ──
            for wo in rec.workorder_ids.filtered(lambda w: w.state not in ('done', 'cancel')):
                has_template = self.env['quality.check'].search([
                    ('workorder_id', '=', wo.id),
                    ('employee_id', '=', False),
                ], limit=1)
                if not has_template:
                    try:
                        self.env['quality.check'].sudo().create({
                            'workorder_id': wo.id,
                            'workcenter_id': wo.workcenter_id.id,
                            'product_id': rec.product_id.id,
                            'title': 'Autocontrôle',
                            'test_type': 'passfail',
                            'quality_state': 'none',
                        })
                    except Exception:
                        pass  # module quality non installé ou champs manquants
        return True

    def action_retirer_lancer(self):
        """Retire le flag 'Lancé' de l'OF."""
        self.write({'is_lancer': False})
        return True
