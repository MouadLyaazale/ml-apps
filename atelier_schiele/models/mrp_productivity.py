from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Technicien',
        index=True,
        ondelete='restrict',
    )

    def action_open_time_correction(self):
        """Ouvre le wizard de correction de temps pour ce bloc."""
        self.ensure_one()
        return {
            'name': 'Correction de temps',
            'type': 'ir.actions.act_window',
            'res_model': 'atelier.time.correction',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_productivity_id': self.id},
        }

    def action_atelier_force_close(self):
        """Bouton superviseur : clôture ce bloc de productivité ouvert."""
        for rec in self:
            if rec.date_end:
                raise UserError(_("Ce bloc est déjà clôturé."))
            now = fields.Datetime.now()
            rec.write({'date_end': now})
            rec._compute_duration()
            mo = rec.workorder_id.production_id
            if mo:
                mo.message_post(body=_(
                    "⚠️ Clôture forcée (backend) par %(user)s : %(emp)s – %(op)s",
                    user=self.env.user.name,
                    emp=rec.employee_id.name,
                    op=rec.workorder_id.name,
                ))
        return True
