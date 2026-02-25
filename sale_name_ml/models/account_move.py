from odoo import models, fields

class AccountMove(models.Model):
    _inherit = "account.move"

    x_real_customer_name = fields.Char(string="Nom client reel")
