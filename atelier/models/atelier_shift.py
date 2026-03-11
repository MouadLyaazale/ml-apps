from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AtelierShift(models.Model):
    _name = 'atelier.shift'
    _description = 'Vacation / Équipe atelier'
    _order = 'start_hour asc'

    name = fields.Char(required=True, string='Nom de la vacation')
    start_hour = fields.Float(required=True, string='Heure début',
                              help='Ex: 8.0 = 08:00, 13.5 = 13:30')
    end_hour = fields.Float(required=True, string='Heure fin')
    auto_close_timers = fields.Boolean(
        default=True,
        string='Fermeture auto des chronos',
        help="Clôture automatiquement les blocs de temps ouverts à la fin de cette vacation.",
    )
    active = fields.Boolean(default=True)
    employee_ids = fields.Many2many(
        'hr.employee',
        'atelier_shift_employee_rel',
        'shift_id', 'employee_id',
        string='Techniciens de cette vacation',
    )
    color = fields.Integer(default=0, string='Couleur')

    @api.constrains('start_hour', 'end_hour')
    def _check_hours(self):
        for rec in self:
            if rec.start_hour >= rec.end_hour:
                raise ValidationError(_("L'heure de fin doit être supérieure à l'heure de début."))
            if not (0.0 <= rec.start_hour <= 23.99) or not (0.0 <= rec.end_hour <= 24.0):
                raise ValidationError(_("Les heures doivent être comprises entre 0 et 24."))

    def name_get(self):
        result = []
        for rec in self:
            h_start = '%02d:%02d' % (int(rec.start_hour), int(round((rec.start_hour % 1) * 60)))
            h_end   = '%02d:%02d' % (int(rec.end_hour),   int(round((rec.end_hour   % 1) * 60)))
            result.append((rec.id, '%s (%s – %s)' % (rec.name, h_start, h_end)))
        return result

    def close_open_blocks(self):
        """Ferme les blocs de productivité ouverts dont le début remonte à cette vacation."""
        from datetime import datetime, date
        today = date.today()
        for shift in self.filtered('auto_close_timers'):
            sh = int(shift.start_hour)
            sm = int(round((shift.start_hour % 1) * 60))
            eh = int(shift.end_hour)
            em = int(round((shift.end_hour   % 1) * 60))
            shift_start_dt = datetime(today.year, today.month, today.day, sh, sm, 0)
            shift_end_dt   = datetime(today.year, today.month, today.day, eh, em, 0)
            open_blocks = self.env['mrp.workcenter.productivity'].search([
                ('date_end', '=', False),
                ('date_start', '>=', fields.Datetime.to_string(shift_start_dt)),
                ('date_start', '<=', fields.Datetime.to_string(shift_end_dt)),
            ])
            if open_blocks:
                open_blocks.write({'date_end': fields.Datetime.to_string(shift_end_dt)})
                open_blocks._compute_duration()
