# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http  
from odoo.http import request  


class EmployeePinController(http.Controller):

    @http.route('/pos/check_employee_pin', type='json', auth='public')
    def check_employee_pin(self, pin):

        matching_employees = request.env['hr.employee'].sudo().search([('pin', '=', pin)])
        for emp in matching_employees:
            return {
                'id': emp.id,
                'name': emp.name,
                'discount_approval': emp.discount_approval,
                'price_approval': emp.price_approval,
            }
