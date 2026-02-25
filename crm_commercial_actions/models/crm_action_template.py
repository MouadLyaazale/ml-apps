from odoo import fields, models

class CrmActionTemplate(models.Model):
    _name = "crm.action.template"
    _description = "CRM Commercial Actions Template"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    line_ids = fields.One2many("crm.action.template.line", "template_id")


class CrmActionTemplateLine(models.Model):
    _name = "crm.action.template.line"
    _description = "CRM Commercial Actions Template Line"
    _order = "sequence"

    sequence = fields.Integer(default=10)
    template_id = fields.Many2one("crm.action.template", required=True, ondelete="cascade")
    label = fields.Char(required=True)
    value_type = fields.Selection(
        [
            ("char", "Text"),
            ("date", "Date"),
            ("datetime", "Datetime"),
            ("float", "Number"),
            ("boolean", "Yes/No"),
        ],
        default="char",
        required=True,
    )
