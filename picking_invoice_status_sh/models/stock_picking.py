from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ml_statut_facturation = fields.Selection(
        selection=[
            ("invoiced", "Facturé"),
            ("to_invoice", "Prêt à facturer"),
            ("not_ready", "Non prêt à facturer"),
        ],
        string="Statut de facturation",
        compute="_compute_ml_statut_facturation",
        store=True,
        compute_sudo=True,
        readonly=True,
    )

    def _get_ml_status_map(self):
        pickings = self
        res = {p.id: "not_ready" for p in pickings}

        done_pickings = pickings.filtered(lambda p: p.state == "done")
        if not done_pickings:
            return res

        AccountMove = self.env["account.move"].sudo()

        # 1) Softhealer: factures liées via sh_picking_ids
        moves = self.env["account.move"]
        if "sh_picking_ids" in moves._fields:
            moves = AccountMove.search([
                ("move_type", "in", ("out_invoice", "out_refund")),
                ("state", "!=", "cancel"),
                ("sh_picking_ids", "in", done_pickings.ids),
            ])
        else:
            moves = self.env["account.move"]

        invoiced_by_sh = set()
        for mv in moves:
            for p in mv.sh_picking_ids:
                if p.id in res:
                    invoiced_by_sh.add(p.id)

        for pid in invoiced_by_sh:
            res[pid] = "invoiced"

        # 2) Odoo standard: basé sur quantités facturées vs livrées sur les lignes de vente
        eps = 1e-6
        for picking in done_pickings:
            if res[picking.id] == "invoiced":
                continue

            sale_lines = picking.move_ids.mapped("sale_line_id").filtered(bool)
            if not sale_lines:
                continue

            delivered_lines = sale_lines.filtered(lambda l: (l.qty_delivered or 0.0) > 0.0)
            if not delivered_lines:
                continue

            all_covered = all((l.qty_invoiced or 0.0) + eps >= (l.qty_delivered or 0.0) for l in delivered_lines)
            any_missing = any((l.qty_invoiced or 0.0) + eps < (l.qty_delivered or 0.0) for l in delivered_lines)

            if all_covered:
                res[picking.id] = "invoiced"
            elif any_missing:
                res[picking.id] = "to_invoice"
            else:
                res[picking.id] = "not_ready"

        return res

    @api.depends(
        "state",
        "move_ids",
        "move_ids.sale_line_id",
        "move_ids.sale_line_id.qty_delivered",
        "move_ids.sale_line_id.qty_invoiced",
    )
    def _compute_ml_statut_facturation(self):
        status_map = self._get_ml_status_map()
        for picking in self:
            picking.ml_statut_facturation = status_map.get(picking.id, "not_ready")
