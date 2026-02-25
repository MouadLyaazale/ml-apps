from odoo import fields, models


class SaleOrderLineLog(models.Model):
    _name = 'sale.order.line.log'
    _description = 'Sale Order Line Change Log'
    _order = 'write_date desc'

    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line',
        required=True,
        ondelete='cascade',
    )
    order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        related='order_line_id.order_id',
        store=True,
    )
    field_name = fields.Char(string='Field', required=True)
    field_description = fields.Char(string='Field Label')
    old_value = fields.Char(string='Old Value')
    new_value = fields.Char(string='New Value')
    user_id = fields.Many2one(
        'res.users',
        string='Changed By',
        default=lambda self: self.env.user,
    )
    write_date = fields.Datetime(string='Change Date', readonly=True)
