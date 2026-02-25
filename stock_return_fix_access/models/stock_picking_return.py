# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api

class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def action_create_returns(self):
        """
        Override to allow non-privileged users to create returns even if
        product.product write access is restricted.
        """
        # Execute the original method with elevated privileges (sudo)
        return super(StockReturnPicking, self.sudo()).action_create_returns()
