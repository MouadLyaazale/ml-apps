from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AtelierTimeCorrection(models.TransientModel):
    _name = 'atelier.time.correction'
    _description = 'Correction de bloc de temps atelier'

    productivity_id = fields.Many2one(
        'mrp.workcenter.productivity',
        string='Bloc de temps',
        required=True,
        ondelete='cascade',
    )
    employee_id = fields.Many2one(
        related='productivity_id.employee_id',
        string='Technicien', readonly=True,
    )
    workorder_id = fields.Many2one(
        related='productivity_id.workorder_id',
        string='Opération', readonly=True,
    )
    production_id = fields.Many2one(
        related='productivity_id.workorder_id.production_id',
        string='OF', readonly=True,
    )
    date_start_original = fields.Datetime(
        related='productivity_id.date_start',
        string='Début original', readonly=True,
    )
    date_end_original = fields.Datetime(
        related='productivity_id.date_end',
        string='Fin originale', readonly=True,
    )
    date_start = fields.Datetime(required=True, string='Nouveau début')
    date_end   = fields.Datetime(string='Nouvelle fin')
    reason     = fields.Char(required=True, string='Motif de correction')

    @api.onchange('productivity_id')
    def _onchange_productivity(self):
        if self.productivity_id:
            self.date_start = self.productivity_id.date_start
            self.date_end   = self.productivity_id.date_end

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_end and rec.date_start >= rec.date_end:
                raise ValidationError(_("Le début doit être antérieur à la fin."))

    def action_apply(self):
        self.ensure_one()
        self.productivity_id.write({
            'date_start': self.date_start,
            'date_end':   self.date_end,
        })
        if self.date_end:
            self.productivity_id._compute_duration()
        # Traçabilité dans le chatter de l'OF
        mo = self.productivity_id.workorder_id.production_id
        if mo:
            mo.message_post(body=_(
                "⏱ Correction de temps par %(user)s :<br/>"
                "Technicien : <b>%(emp)s</b> — Opération : <b>%(op)s</b><br/>"
                "Motif : %(reason)s",
                user=self.env.user.name,
                emp=self.employee_id.name,
                op=self.workorder_id.name,
                reason=self.reason,
            ))
        return {'type': 'ir.actions.act_window_close'}
