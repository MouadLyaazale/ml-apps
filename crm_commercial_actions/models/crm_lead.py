from odoo import api, fields, models
from markupsafe import Markup, escape

class CrmLead(models.Model):
    _inherit = "crm.lead"

    action_template_id = fields.Many2one("crm.action.template", string="Commercial Actions Template")
    action_line_ids = fields.One2many("crm.lead.action.line", "lead_id", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        for lead in leads:
            template = lead.action_template_id
            if not template:
                template = self.env["crm.action.template"].search([("active", "=", True)], limit=1)
                if template:
                    lead.action_template_id = template.id

            if template and not lead.action_line_ids:
                lead.action_line_ids = [(0, 0, {
                    "sequence": l.sequence,
                    "label": l.label,
                    "value_type": l.value_type,
                }) for l in template.line_ids]
        return leads

    def action_move_suivi_to_note(self):
        for lead in self:
            if not lead.action_line_ids:
                continue

            lines = []
            for line in lead.action_line_ids.sorted("sequence"):
                value = line._get_value_as_text()
                if value:
                    lines.append((line.label, value))

            if not lines:
                continue

            stamp = fields.Datetime.to_string(fields.Datetime.now())
            list_items = "".join(
                f"<li><strong>{escape(label)}:</strong> {escape(value)}</li>"
                for label, value in lines
            )
            block = Markup(
                "<div style=\"margin-bottom:8px;\">"
                "<p><strong>Suivi - {stamp}</strong></p>"
                "<ul>{items}</ul>"
                "<hr/>"
                "</div>"
            ).format(stamp=escape(stamp), items=Markup(list_items))

            lead.description = Markup("{}{}" ).format(block, Markup(lead.description or ""))
            lead.action_line_ids._clear_typed_value()

        return True
