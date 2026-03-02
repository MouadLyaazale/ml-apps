# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    pos_config_id = fields.Many2one(
        'pos.config',
        string="POS Configuration")
    
    discount_limit = fields.Float(string="Set Disocunt Limit" , readonly=False , related='pos_config_id.discount_limit')
    access_discount_limit = fields.Boolean(string="Access the discount on order line" , readonly=False , related='pos_config_id.access_discount_limit')

    price_limit = fields.Float(string="Minimum Price (%)" , readonly=False , related='pos_config_id.price_limit')
    access_price_limit = fields.Boolean(string="Restrict minimum price on order line" , readonly=False , related='pos_config_id.access_price_limit')