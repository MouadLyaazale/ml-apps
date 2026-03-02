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

    show_stock_qty = fields.Boolean(
        string="Show Available Stock in POS",
        help="Display the free-to-sell stock quantity (on-hand minus reservations) on each product card. Stock is filtered to this POS's warehouse."
    )

    show_bl_a4 = fields.Boolean(
        string="Show 'Print A4 BL' Button",
        help="Show a button on the receipt screen to print the Bon de Livraison in A4 format."
    )
    bl_docx_template_id = fields.Integer(
        string="BL Docx Template ID",
        default=1,
        help="ID of the docx.template record to use for A4 BL printing (default 1 = SCHIELE)."
    )