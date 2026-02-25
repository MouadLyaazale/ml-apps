from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    divers_partner_id = fields.Many2one("res.partner", string="Contact Divers")
