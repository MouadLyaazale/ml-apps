# -*- coding: utf-8 -*-
from odoo import models, api, fields

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_vat_account_345520 = fields.Boolean(
        string='Is VAT Account 345520',
        compute='_compute_is_vat_account_345520',
        store=False,
    )

    @api.depends('account_id.code')
    def _compute_is_vat_account_345520(self):
        for line in self:
            line.is_vat_account_345520 = line.account_id.code == '345520'

    def action_force_vat_declaration_from_matching(self):
        """
        Force VAT declaration from bank matching interface.
        Applies VAT tax tags to the move line for account 345520.
        """
        self.ensure_one()
        
        if self.account_id.code != '345520':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'This action is only for account 345520 (État - TVA récupérable)',
                    'type': 'danger'
                }
            }
        
        # Get VAT tax tags
        domain = [
            ('applicability', '=', 'taxes'),
            ('country_id', '=', self.company_id.country_id.id)
        ]
        vat_tags = self.env['account.account.tag'].search(domain)
        
        if not vat_tags:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Info',
                    'message': 'No VAT tax tags found for your country',
                    'type': 'info'
                }
            }
        
        # Apply VAT tags directly
        current_tags = self.tax_tag_ids
        new_tags = current_tags | vat_tags
        self.write({'tax_tag_ids': [(6, 0, new_tags.ids)]})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'VAT Declaration applied for amount: {self.amount_currency} {self.currency_id.name}',
                'type': 'success'
            }
        }
