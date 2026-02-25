from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PosChangePaymentsWizard(models.TransientModel):
    _name = "pos.change.payments.wizard"
    _description = "POS Change Payments Wizard (Force/SQL)"

    order_id = fields.Many2one("pos.order", required=True, readonly=True)
    line_ids = fields.One2many("pos.change.payments.wizard.line", "wizard_id", string="Payments")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order = self.env["pos.order"].browse(self.env.context.get("active_id"))
        if order:
            res["order_id"] = order.id
            res["line_ids"] = [(0, 0, {
                "payment_method_id": p.payment_method_id.id,
                "amount": p.amount,
            }) for p in order.payment_ids]
        return res

    def action_apply(self):
        self.ensure_one()
        order = self.order_id

        # Require open session (your rule)
        if not order.session_id or order.session_id.state != "opened":
            raise UserError(_("POS session must be open to change payments."))

        # Block negative amounts
        for l in self.line_ids:
            if l.amount < 0:
                raise ValidationError(_("Negative payment lines are not allowed."))

        # Total must match order total
        total = sum(self.line_ids.mapped("amount"))
        if abs(total - order.amount_total) > 0.01:
            raise ValidationError(_("Payments must equal the order total."))

        cr = self.env.cr

        # Discover pos_payment columns (compat across builds)
        cr.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='pos_payment'
        """)
        cols = {r[0] for r in cr.fetchall()}

        def has(c): return c in cols

        # Find id sequence if any
        cr.execute("SELECT pg_get_serial_sequence('pos_payment','id')")
        seq = cr.fetchone()[0]

        # Delete existing payments for this order (SQL bypasses ORM constraints)
        cr.execute("DELETE FROM pos_payment WHERE pos_order_id = %s", (order.id,))

        now = fields.Datetime.now()
        uid = self.env.uid

        # Base values only if columns exist
        base_vals = {}
        if has("pos_order_id"):
            base_vals["pos_order_id"] = order.id
        if has("payment_date"):
            base_vals["payment_date"] = now
        if has("company_id") and order.company_id:
            base_vals["company_id"] = order.company_id.id
        if has("currency_id") and order.currency_id:
            base_vals["currency_id"] = order.currency_id.id
        if has("create_uid"):
            base_vals["create_uid"] = uid
        if has("write_uid"):
            base_vals["write_uid"] = uid
        if has("create_date"):
            base_vals["create_date"] = now
        if has("write_date"):
            base_vals["write_date"] = now

        for l in self.line_ids:
            vals = dict(base_vals)
            if has("payment_method_id"):
                vals["payment_method_id"] = l.payment_method_id.id
            if has("amount"):
                vals["amount"] = l.amount

            columns = list(vals.keys())
            placeholders = ["%s"] * len(vals)

            if has("id"):
                columns = ["id"] + columns
                id_expr = f"nextval('{seq}')" if seq else "DEFAULT"
                sql = "INSERT INTO pos_payment (%s) VALUES (%s)" % (
                    ",".join(columns),
                    ",".join([id_expr] + placeholders),
                )
                cr.execute(sql, tuple(vals.values()))
            else:
                sql = "INSERT INTO pos_payment (%s) VALUES (%s)" % (
                    ",".join(columns),
                    ",".join(placeholders),
                )
                cr.execute(sql, tuple(vals.values()))

        # Refresh cache
        self.env["pos.order"].invalidate_model(["payment_ids"])
        self.env["pos.payment"].invalidate_model()

        return {"type": "ir.actions.act_window_close"}


class PosChangePaymentsWizardLine(models.TransientModel):
    _name = "pos.change.payments.wizard.line"
    _description = "POS Change Payments Wizard Line"

    wizard_id = fields.Many2one("pos.change.payments.wizard", required=True, ondelete="cascade")
    payment_method_id = fields.Many2one("pos.payment.method", required=True)
    amount = fields.Monetary(currency_field="currency_id", required=True)
    currency_id = fields.Many2one(related="wizard_id.order_id.currency_id", readonly=True)
