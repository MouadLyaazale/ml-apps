from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    divers_partner_id = fields.Many2one(
        related="company_id.divers_partner_id",
        readonly=False,
        string="Contact Divers",
    )
