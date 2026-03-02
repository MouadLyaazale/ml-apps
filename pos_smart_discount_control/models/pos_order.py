import logging
from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def action_open_change_payments_wizard(self):
        self.ensure_one()
        action = self.env.ref("pos_smart_discount_control.action_change_payments_wizard").read()[0]
        action["context"] = {"active_id": self.id}
        return action

    @api.model
    def _load_pos_data_read(self, records, config):
        """
        Inject the non-stored computed field `failed_pickings` into every
        pos.order row that comes back from the sync call so the POS frontend
        can decide whether to show the receipt screen.
        """
        result = super()._load_pos_data_read(records, config)
        # Build a quick id→record map to fetch the computed value efficiently.
        by_id = {r.id: r for r in records}
        for row in result:
            order = by_id.get(row.get('id'))
            row['failed_pickings'] = order.failed_pickings if order else False
        return result

    def action_pos_order_invoice(self):
        """
        Block invoice creation when any stock transfer is still pending.
        """
        for order in self:
            if order.failed_pickings:
                raise ValidationError(_(
                    'The invoice cannot be generated for order "%s" because '
                    'one or more stock transfers are not yet validated. '
                    'Please finalise the delivery first.'
                ) % order.name)
        return super().action_pos_order_invoice()
