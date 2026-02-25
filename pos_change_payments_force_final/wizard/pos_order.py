from odoo import models

class PosOrder(models.Model):
    _inherit = "pos.order"

    def action_open_change_payments_wizard_force_final(self):
        self.ensure_one()
        action = self.env.ref("pos_change_payments_force_final.action_wizard").read()[0]
        action["context"] = {"active_id": self.id}
        return action
