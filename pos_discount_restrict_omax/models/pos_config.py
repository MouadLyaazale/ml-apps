# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    discount_limit = fields.Float(string="Set Disocunt Limit")
    access_discount_limit = fields.Boolean(string="Access the discount on order line")

    price_limit = fields.Float(
        string="Minimum Price (%)",
        help="Minimum price allowed as a percentage of the product's sale price. E.g. 80 means the cashier cannot go below 80% of the list price without approval."
    )
    access_price_limit = fields.Boolean(string="Restrict minimum price on order line")