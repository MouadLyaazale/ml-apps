# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'
    
    discount_approval = fields.Boolean(string="Discount Approval", groups="hr.group_hr_user")
    price_approval = fields.Boolean(string="Price Override Approval", groups="hr.group_hr_user")
