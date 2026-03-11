from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    # ------------------------------------------------------------------ #
    # Atelier kiosk helpers                                                #
    # ------------------------------------------------------------------ #

    def atelier_start(self, employee_id):
        """Démarre le chrono pour un technicien sur cette opération.
        
        Règle stricte : un technicien ne peut avoir qu'UN SEUL bloc ouvert à la fois,
        peu importe l'OF ou l'opération. Utilise un verrou DB (SELECT FOR UPDATE NOWAIT)
        pour éviter les doublons en charge concurrente (30 techniciens simultanés).
        """
        self.ensure_one()
        employee = self.env['hr.employee'].browse(employee_id)
        if not employee.exists():
            raise UserError(_("Technicien introuvable."))

        if self.state in ('done', 'cancel'):
            raise UserError(_("Cette opération est terminée ou annulée."))

        # ── Verrou DB au niveau de l'employé pour éviter les race conditions ──
        # On verrouille toutes les lignes de productivité ouvertes de cet employé.
        # NOWAIT = échoue immédiatement si une autre transaction tient le verrou.
        self.env.cr.execute(
            """
            SELECT id FROM mrp_workcenter_productivity
            WHERE employee_id = %s AND date_end IS NULL
            FOR UPDATE NOWAIT
            """,
            (employee_id,)
        )

        # ── Une seule opération à la fois – toutes opérations, tous OFs ──
        open_blocks = self.env['mrp.workcenter.productivity'].search([
            ('employee_id', '=', employee_id),
            ('date_end', '=', False),
        ])
        if open_blocks:
            # Si ce technicien a déjà un bloc ouvert sur CET opération, c'est ok (idempotent)
            already_on_this = open_blocks.filtered(lambda b: b.workorder_id.id == self.id)
            if already_on_this:
                return True  # déjà en cours sur cette opération
            # Sur une autre opération → bloquer
            other = open_blocks[0]
            op_name = other.workorder_id.name if other.workorder_id else '—'
            mo_name = (other.workorder_id.production_id.name
                       if other.workorder_id and other.workorder_id.production_id else '—')
            raise UserError(_(
                "Vous êtes déjà en cours sur l'opération « %(op)s » (%(mo)s). "
                "Mettez-la en pause avant de démarrer une autre opération.",
                op=op_name,
                mo=mo_name,
            ))

        # ── Forcer la transition d'état si nécessaire ──
        if self.state != 'progress':
            try:
                if self.state == 'pending':
                    self.write({'state': 'ready'})
                self._start_timer()
            except Exception:
                pass  # forcer la création du bloc même si la transition échoue

        # ── Créer le bloc de productivité ──
        self.env['mrp.workcenter.productivity'].create({
            'workcenter_id': self.workcenter_id.id,
            'workorder_id': self.id,
            'employee_id': employee_id,
            'date_start': fields.Datetime.now(),
            'loss_id': self._get_productive_loss_id(),
        })
        return True

    def atelier_pause(self, employee_id):
        """Met en pause le chrono du technicien sur cette opération."""
        self.ensure_one()
        open_block = self.env['mrp.workcenter.productivity'].search([
            ('workorder_id', '=', self.id),
            ('employee_id', '=', employee_id),
            ('date_end', '=', False),
        ], limit=1)
        if open_block:
            open_block.date_end = fields.Datetime.now()
            open_block._compute_duration()
            # Recalculer la durée totale sur le work order
            self._compute_duration()
        return True

    def atelier_stop(self, employee_id):
        """Arrête le chrono et clôture l'opération pour ce technicien."""
        self.ensure_one()
        self.atelier_pause(employee_id)
        # Si c'est le dernier technicien actif, marquer ready/done
        still_open = self.env['mrp.workcenter.productivity'].search([
            ('workorder_id', '=', self.id),
            ('date_end', '=', False),
        ])
        if not still_open:
            self._stop_timer()
        return True

    @api.model
    def _cron_close_shift_timers(self):
        """Cron planifié : ferme les chronos ouverts pour les vacations terminées."""
        shifts = self.env['atelier.shift'].search([('active', '=', True)])
        shifts.close_open_blocks()

    def _get_productive_loss_id(self):
        """Retourne la perte de type 'productive' pour le centre de travail."""
        loss = self.env['mrp.workcenter.productivity.loss'].search([
            ('loss_type', '=', 'productive'),
        ], limit=1)
        if not loss:
            loss = self.env['mrp.workcenter.productivity.loss'].search([], limit=1)
        return loss.id if loss else False
