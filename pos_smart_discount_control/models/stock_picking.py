# -*- coding: utf-8 -*-
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def write(self, vals):
        """
        After a POS-related transfer reaches the 'done' state, check whether
        ALL transfers for the linked POS order are now complete.  If so, and
        if no invoice exists yet, generate the invoice automatically.

        This covers all paths that mark a picking as done:
          - button_validate (with or without backorder wizard)
          - immediate-transfer wizard
          - programmatic validation
        """
        result = super().write(vals)
        if vals.get('state') == 'done':
            for picking in self:
                order = picking.pos_order_id
                if order:
                    order._auto_invoice_on_picking_done()
        return result
