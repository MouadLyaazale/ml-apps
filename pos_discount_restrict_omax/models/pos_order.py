from odoo import models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def action_open_change_payments_wizard(self):
        self.ensure_one()
        action = self.env.ref("pos_discount_restrict_omax.action_change_payments_wizard").read()[0]
        action["context"] = {"active_id": self.id}
        return action
