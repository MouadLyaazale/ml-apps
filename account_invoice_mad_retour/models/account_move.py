import re

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    amount_total_mad = fields.Float(
        string="Total MAD",
        compute="_compute_amount_total_mad",
        store=True,
        digits="Account",
        help="Invoice total in company currency (MAD) without currency symbol.",
    )
    retour_sur_bl = fields.Char(
        string="Retour sur (BL)",
        compute="_compute_retour_sur_bl",
        help="Delivery orders linked to the original invoice reversed by this credit note.",
    )

    @api.depends("amount_total_signed")
    def _compute_amount_total_mad(self):
        for move in self:
            move.amount_total_mad = move.amount_total_signed or 0.0

    @api.depends(
        "move_type",
        "reversed_entry_id",
        "reversed_entry_id.invoice_line_ids",
        "sh_picking_ids",
        "reversed_entry_id.sh_picking_ids",
    )
    def _compute_retour_sur_bl(self):
        StockPicking = self.env["stock.picking"]
        for move in self:
            move.retour_sur_bl = False
            if move.move_type not in ("out_refund", "in_refund"):
                continue

            source_pickings = self.env["stock.picking"]
            if "sh_picking_ids" in move._fields and move.sh_picking_ids:
                source_pickings |= move.sh_picking_ids
            elif move.reversed_entry_id and "sh_picking_ids" in move.reversed_entry_id._fields:
                source_pickings |= move.reversed_entry_id.sh_picking_ids

            if not source_pickings and move.reversed_entry_id:
                original_move = move.reversed_entry_id
                move_line_model = self.env["account.move.line"]
                if "sale_line_ids" in move_line_model._fields:
                    source_pickings |= original_move.invoice_line_ids.sale_line_ids.move_ids.mapped("picking_id")
                if "purchase_line_id" in move_line_model._fields:
                    source_pickings |= original_move.invoice_line_ids.purchase_line_id.move_ids.mapped("picking_id")

            source_pickings = source_pickings.filtered(lambda picking: picking)
            out_pickings = source_pickings.filtered(lambda picking: picking.picking_type_code == "outgoing")

            in_pickings = source_pickings.filtered(lambda picking: picking.picking_type_code == "incoming")
            for in_picking in in_pickings:
                move_field_name = "move_ids_without_package" if "move_ids_without_package" in in_picking._fields else "move_ids"
                returned_out_pickings = in_picking[move_field_name].mapped("origin_returned_move_id.picking_id").filtered(
                    lambda picking: picking and picking.picking_type_code == "outgoing"
                )
                out_pickings |= returned_out_pickings

                if not returned_out_pickings and in_picking.origin:
                    out_names = set(re.findall(r"[A-Za-z0-9]+/OUT/[0-9]+", in_picking.origin))
                    if out_names:
                        out_pickings |= StockPicking.search([("name", "in", list(out_names))])

            if not out_pickings and move.reversed_entry_id and "sh_picking_ids" in move.reversed_entry_id._fields:
                out_pickings |= move.reversed_entry_id.sh_picking_ids.filtered(lambda picking: picking.picking_type_code == "outgoing")

            result_names = out_pickings.mapped("name") or source_pickings.mapped("name")
            move.retour_sur_bl = ", ".join(sorted(name for name in result_names if name)) or False
