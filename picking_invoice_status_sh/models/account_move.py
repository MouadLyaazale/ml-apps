from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _recompute_linked_picking_invoice_status(self, extra_pickings=None):
        StockPicking = self.env["stock.picking"]
        pickings = extra_pickings or StockPicking
        if "sh_picking_ids" in self._fields:
            pickings |= self.sudo().mapped("sh_picking_ids")

        pickings = pickings.filtered(lambda picking: picking)
        if not pickings or "ml_statut_facturation" not in StockPicking._fields:
            return

        field = StockPicking._fields["ml_statut_facturation"]
        self.env.add_to_compute(field, pickings)
        pickings._recompute_recordset(["ml_statut_facturation"])

    def create(self, vals_list):
        records = super().create(vals_list)
        records._recompute_linked_picking_invoice_status()
        return records

    def write(self, vals):
        before_pickings = self.env["stock.picking"]
        if "sh_picking_ids" in self._fields:
            before_pickings = self.sudo().mapped("sh_picking_ids")

        result = super().write(vals)

        after_pickings = self.env["stock.picking"]
        if "sh_picking_ids" in self._fields:
            after_pickings = self.sudo().mapped("sh_picking_ids")

        self._recompute_linked_picking_invoice_status(extra_pickings=(before_pickings | after_pickings))
        return result

    def unlink(self):
        linked_pickings = self.env["stock.picking"]
        if "sh_picking_ids" in self._fields:
            linked_pickings = self.sudo().mapped("sh_picking_ids")

        result = super().unlink()
        self._recompute_linked_picking_invoice_status(extra_pickings=linked_pickings)
        return result
