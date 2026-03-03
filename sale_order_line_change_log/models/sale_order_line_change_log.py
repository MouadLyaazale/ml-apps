from markupsafe import Markup
from odoo import models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _sol_log_snapshot(self):
        """Return a snapshot dict of all current order lines keyed by line id."""
        snapshot = {}
        for order in self:
            snapshot[order.id] = {
                line.id: {
                    "product": line.product_id.display_name or "-",
                    "name": (line.name or "").strip(),
                    "qty": line.product_uom_qty,
                    "uom": line.product_uom_id.name or "-",
                    "price_unit": line.price_unit,
                    "discount": line.discount,
                    "taxes": ", ".join(line.tax_ids.mapped("name")) or "-",
                }
                for line in order.order_line
            }
        return snapshot

    def _sol_format_price(self, amount, currency):
        """Format a price with its currency symbol."""
        if currency:
            return f"{amount:,.{currency.decimal_places}f} {currency.symbol}"
        return str(amount)

    def write(self, vals):
        # Guard: skip snapshot work when order_line is not being modified.
        # order_line commands arrive as a list; any other key is irrelevant for line logging.
        if "order_line" not in vals:
            return super().write(vals)

        # Snapshot AVANT modification
        before_data = self._sol_log_snapshot()

        res = super().write(vals)

        # Apres le write, on compare
        for order in self:
            currency = order.currency_id
            changes = []

            after_lines = {
                line.id: {
                    "product": line.product_id.display_name or "-",
                    "name": (line.name or "").strip(),
                    "qty": line.product_uom_qty,
                    "uom": line.product_uom_id.name or "-",
                    "price_unit": line.price_unit,
                    "discount": line.discount,
                    "taxes": ", ".join(line.tax_ids.mapped("name")) or "-",
                }
                for line in order.order_line
            }

            before_lines = before_data.get(order.id, {})

            # Lignes supprimées
            for line_id in set(before_lines) - set(after_lines):
                b = before_lines[line_id]
                changes.append(
                    "<li><b style='color:#cc0000'>&#10060; Ligne supprimée</b> : "
                    f"{b['product']} "
                    f"(Qté&nbsp;{b['qty']}&nbsp;{b['uom']}, "
                    f"PU&nbsp;{self._sol_format_price(b['price_unit'], currency)}, "
                    f"Remise&nbsp;{b['discount']}%, "
                    f"Taxes:&nbsp;{b['taxes']})</li>"
                )

            # Lignes ajoutées
            for line_id in set(after_lines) - set(before_lines):
                a = after_lines[line_id]
                changes.append(
                    "<li><b style='color:#007700'>&#10003; Nouvelle ligne</b> : "
                    f"{a['product']} "
                    f"(Qté&nbsp;{a['qty']}&nbsp;{a['uom']}, "
                    f"PU&nbsp;{self._sol_format_price(a['price_unit'], currency)}, "
                    f"Remise&nbsp;{a['discount']}%, "
                    f"Taxes:&nbsp;{a['taxes']})</li>"
                )

            # Lignes modifiées
            for line_id in set(after_lines) & set(before_lines):
                b = before_lines[line_id]
                a = after_lines[line_id]
                field_changes = []

                if b["name"] != a["name"]:
                    field_changes.append(
                        _("Description : <i>%s</i> → <i>%s</i>") % (b["name"] or "—", a["name"] or "—")
                    )
                if b["qty"] != a["qty"] or b["uom"] != a["uom"]:
                    field_changes.append(
                        _("Qté : %s %s → %s %s")
                        % (b["qty"], b["uom"], a["qty"], a["uom"])
                    )
                if b["price_unit"] != a["price_unit"]:
                    field_changes.append(
                        _("PU : %s → %s")
                        % (
                            self._sol_format_price(b["price_unit"], currency),
                            self._sol_format_price(a["price_unit"], currency),
                        )
                    )
                if b["discount"] != a["discount"]:
                    field_changes.append(
                        _("Remise : %s%% → %s%%") % (b["discount"], a["discount"])
                    )
                if b["taxes"] != a["taxes"]:
                    field_changes.append(
                        _("Taxes : %s → %s") % (b["taxes"], a["taxes"])
                    )

                if field_changes:
                    changes.append(
                        f"<li><b>&#9998; Ligne modifiée</b> ({a['product']}) :"
                        f"<ul>{''.join(f'<li>{c}</li>' for c in field_changes)}</ul></li>"
                    )

            if changes:
                message = Markup(
                    "<b>Modifications des lignes de commande :</b>"
                    "<ul>{}</ul>"
                ).format(Markup("").join(Markup(c) for c in changes))
                order.message_post(
                    body=message,
                    subtype_xmlid="mail.mt_note",
                )

        return res
