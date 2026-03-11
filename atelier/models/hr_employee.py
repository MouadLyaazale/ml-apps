from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    atelier_is_supervisor = fields.Boolean(
        string='Superviseur atelier',
        default=False,
        help='Ce technicien a accès au tableau de bord superviseur et aux actions admin kiosque.',
    )
    atelier_shift_id = fields.Many2one(
        'atelier.shift',
        string='Vacation atelier',
        help='Vacation habituelle de ce technicien.',
    )
    atelier_auto_logout_minutes = fields.Integer(
        string='Déconnexion auto (minutes)',
        default=0,
        help='0 = utiliser le réglage global. Valeur > 0 remplace le réglage global pour ce technicien.',
    )

    atelier_pin = fields.Char(
        string='Code PIN Atelier',
        size=6,
        groups='hr.group_hr_user',
        help="Code PIN (4 à 6 chiffres) utilisé pour se connecter au kiosque atelier.",
    )
    atelier_badge_id = fields.Char(
        string='Badge Atelier',
        copy=False,
        help="Numéro de badge scannable sur le kiosque.",
    )

    @api.constrains('atelier_pin')
    def _check_pin(self):
        for emp in self:
            if emp.atelier_pin and not re.fullmatch(r'\d{4,6}', emp.atelier_pin):
                raise ValidationError(
                    _("Le code PIN doit contenir entre 4 et 6 chiffres.")
                )

    @api.constrains('atelier_badge_id')
    def _check_badge_unique(self):
        for emp in self:
            if emp.atelier_badge_id:
                duplicate = self.search([
                    ('atelier_badge_id', '=', emp.atelier_badge_id),
                    ('id', '!=', emp.id),
                ])
                if duplicate:
                    raise ValidationError(
                        _("Le badge '%s' est déjà utilisé par %s.")
                        % (emp.atelier_badge_id, duplicate[0].name)
                    )
