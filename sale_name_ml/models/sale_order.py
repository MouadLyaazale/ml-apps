from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_real_customer_name = fields.Char(string="Nom client reel")
    x_real_customer_address = fields.Text(string="Adresse client reelle")
    x_real_customer_ice = fields.Char(string="ICE client reel")

    x_is_divers = fields.Boolean(compute="_compute_x_is_divers", store=False)

    @api.depends("partner_id", "company_id", "company_id.divers_partner_id")
    def _compute_x_is_divers(self):
        for order in self:
            divers = order.company_id.divers_partner_id
            order.x_is_divers = bool(divers and order.partner_id == divers)

    def action_confirm(self):
        for order in self:
            if order.x_is_divers:
                if not order.x_real_customer_name:
                    raise ValidationError("Veuillez saisir le Nom client reel (client = Divers).")
                if not order.x_real_customer_address:
                    raise ValidationError("Veuillez saisir l'Adresse client reelle (client = Divers).")
        return super().action_confirm()
