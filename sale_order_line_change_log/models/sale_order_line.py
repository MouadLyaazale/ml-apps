from odoo import api, fields, models


TRACKED_FIELDS = {
    'product_id': 'Product',
    'product_uom_qty': 'Quantity',
    'price_unit': 'Unit Price',
    'discount': 'Discount (%)',
    'name': 'Description',
}


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    change_log_ids = fields.One2many(
        'sale.order.line.log',
        'order_line_id',
        string='Change Logs',
    )
    change_log_count = fields.Integer(
        string='Change Log Count',
        compute='_compute_change_log_count',
    )

    @api.depends('change_log_ids')
    def _compute_change_log_count(self):
        for line in self:
            line.change_log_count = len(line.change_log_ids)

    def write(self, vals):
        tracked = {k: v for k, v in vals.items() if k in TRACKED_FIELDS}
        if tracked:
            for line in self:
                for field, label in TRACKED_FIELDS.items():
                    if field not in tracked:
                        continue
                    old_val = line[field]
                    if hasattr(old_val, 'display_name'):
                        old_val = old_val.display_name
                    else:
                        old_val = str(old_val) if old_val is not False else ''
                    new_raw = tracked[field]
                    if isinstance(new_raw, (list, tuple)):
                        new_record = self.env[
                            self._fields[field].comodel_name
                        ].browse(new_raw)
                        new_val = new_record.display_name
                    else:
                        new_val = str(new_raw) if new_raw is not False else ''
                    self.env['sale.order.line.log'].sudo().create({
                        'order_line_id': line.id,
                        'field_name': field,
                        'field_description': label,
                        'old_value': old_val,
                        'new_value': new_val,
                        'user_id': self.env.user.id,
                    })
        return super().write(vals)
