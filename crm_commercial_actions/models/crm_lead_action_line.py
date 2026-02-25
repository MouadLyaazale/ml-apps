from odoo import api, fields, models

class CrmLeadActionLine(models.Model):
    _name = "crm.lead.action.line"
    _description = "CRM Commercial Action Line"
    _order = "sequence"

    sequence = fields.Integer(default=10)
    lead_id = fields.Many2one("crm.lead", required=True, ondelete="cascade")
    label = fields.Char(readonly=True)
    value_type = fields.Selection(
        [
            ("char", "Text"),
            ("date", "Date"),
            ("datetime", "Datetime"),
            ("float", "Number"),
            ("boolean", "Yes/No"),
        ],
        default="char",
        readonly=True,
        required=True,
    )
    value_char = fields.Char()
    value_date = fields.Date()
    value_datetime = fields.Datetime()
    value_float = fields.Float()
    value_boolean = fields.Selection(
        [("yes", "Yes"), ("no", "No")]
    )
    display_value = fields.Char(compute="_compute_display_value")

    @api.depends("value_type", "value_char", "value_date", "value_datetime", "value_float", "value_boolean")
    def _compute_display_value(self):
        for line in self:
            line.display_value = line._get_value_as_text()

    def _get_value_as_text(self):
        self.ensure_one()
        if self.value_type == "date":
            return self.value_date and fields.Date.to_string(self.value_date) or ""
        if self.value_type == "datetime":
            return self.value_datetime and fields.Datetime.to_string(self.value_datetime) or ""
        if self.value_type == "float":
            return self.value_float not in (False, None) and str(self.value_float) or ""
        if self.value_type == "boolean":
            return "Yes" if self.value_boolean == "yes" else ("No" if self.value_boolean == "no" else "")
        return self.value_char or ""

    def _clear_typed_value(self):
        self.write({
            "value_char": False,
            "value_date": False,
            "value_datetime": False,
            "value_float": False,
            "value_boolean": False,
        })
