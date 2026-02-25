from odoo import models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def write(self, vals):
        # Snapshot AVANT modification
        before_data = {}
        for order in self:
            before_data[order.id] = {
                line.id: {
                    "product": line.product_id.display_name,
                    "qty": line.product_uom_qty,
                    "price_unit": line.price_unit,
                    "discount": line.discount,
                    "taxes": ", ".join(line.tax_ids.mapped("name")) or "-",
                }
                for line in order.order_line
            }

        res = super().write(vals)

        # Apres le write, on compare
        for order in self:
            changes = []
            after_lines = {
                line.id: {
                    "product": line.product_id.display_name,
                    "qty": line.product_uom_qty,
                    "price_unit": line.price_unit,
                    "discount": line.discount,
                    "taxes": ", ".join(line.tax_ids.mapped("name")) or "-",
                }
                for line in order.order_line
            }

            before_lines = before_data.get(order.id, {})

            # Lignes supprimer
            removed_ids = set(before_lines.keys()) - set(after_lines.keys())
            for line_id in removed_ids:
                b = before_lines[line_id]
                changes.append(
                    _(
                        "Ligne supprimée : %s (Qté %s, PU %s, Remise %s, Taxes: %s)"
                    )
                    % (b["product"], b["qty"], b["price_unit"], b["discount"], b["taxes"])
                )

            # Lignes ajouter
            added_ids = set(after_lines.keys()) - set(before_lines.keys())
            for line_id in added_ids:
                a = after_lines[line_id]
                changes.append(
                    _(
                        "Nouvelle ligne : %s (Qté %s, PU %s, Remise %s, Taxes: %s)"
                    )
                    % (a["product"], a["qty"], a["price_unit"], a["discount"], a["taxes"])
                )

            # Lignes modifiers
            common_ids = set(after_lines.keys()) & set(before_lines.keys())
            for line_id in common_ids:
                b = before_lines[line_id]
                a = after_lines[line_id]
                line_changes = []
                if b["qty"] != a["qty"]:
                    line_changes.append(_("Qté: %s → %s") % (b["qty"], a["qty"]))
                if b["price_unit"] != a["price_unit"]:
                    line_changes.append(_("PU: %s → %s") % (b["price_unit"], a["price_unit"]))
                if b["discount"] != a["discount"]:
                    line_changes.append(_("Remise: %s → %s") % (b["discount"], a["discount"]))
                if b["taxes"] != a["taxes"]:
                    line_changes.append(_("Taxes: %s → %s") % (b["taxes"], a["taxes"]))
                if line_changes:
                    changes.append(
                        _("Ligne modifiée (%s) : %s")
                        % (a["product"], "; ".join(line_changes))
                    )

            if changes:
                message = "Modifications des lignes de commande :<br/>- " + "<br/>- ".join(
                    changes
                )
                order.message_post(
                    body=message,
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )

        return res
