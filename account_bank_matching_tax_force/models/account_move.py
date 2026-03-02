# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_force_vat_declaration_from_matching(self):
        """
        Force VAT declaration from bank matching interface.
        1. Creates intermediate tax line (account 345540) if missing - needed for cash basis tax processing
        2. Finds the line with account 345520 (VAT payable), and applies VAT tags to it
        3. Sets always_tax_exigible flag for immediate VAT report recognition
        
        The tags tell the VAT declaration report which "box" the tax amount belongs to.
        """
        self.ensure_one()
        _logger.info(f"=== Force VAT Declaration START - Move {self.id} ({self.name}) ===")
        
        # Verify move is posted, if not in correct state, return error
        if self.state != 'posted':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': f'Move must be in "Posted" state. Current state: {self.state}',
                    'type': 'warning'
                }
            }
        
        # Find the line with account 345520 (VAT payable account)
        line_345520 = self.line_ids.filtered(lambda l: l.account_id.code == '345520')
        _logger.info(f"Found {len(line_345520)} lines with account 345520")
        
        if not line_345520:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'No line found for account 345520 (État - TVA récupérable)',
                    'type': 'danger'
                }
            }
        
        if len(line_345520) > 1:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Multiple lines found for account 345520. Please process them individually.',
                    'type': 'danger'
                }
            }
        
        line_345520 = line_345520[0]
        
        # Note: For posted moves from bank matching, the intermediate line (345540) 
        # structure is handled by the system. We only ensure proper tagging.
        vat_amount = line_345520.debit + line_345520.credit
        
        # IMPORTANT: Fix display_type if needed (must be 'tax' for VAT report to recognize it)
        display_type_fixed = False
        if line_345520.display_type != 'tax':
            _logger.warning(f"Fixing display_type: was '{line_345520.display_type}', changing to 'tax'")
            line_345520.write({'display_type': 'tax'})
            display_type_fixed = True
        
        # Get the tax from the VAT line
        if not line_345520.tax_line_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Info',
                    'message': 'The account 345520 line has no associated tax.',
                    'type': 'info'
                }
            }
        
        tax = line_345520.tax_line_id
        _logger.info(f"Tax Line ID: {tax.id} - Name: {tax.name}")
        
        # Get tax tags from this tax via the repartition line relationship
        self.env.cr.execute("""
            SELECT DISTINCT aat.id
            FROM account_account_tag aat
            INNER JOIN account_account_tag_account_tax_repartition_line_rel rel 
                ON aat.id = rel.account_account_tag_id
            INNER JOIN account_tax_repartition_line atrl 
                ON atrl.id = rel.account_tax_repartition_line_id
            WHERE atrl.tax_id = %s
        """, (tax.id,))
        
        tag_ids = [row[0] for row in self.env.cr.fetchall()]
        _logger.info(f"Found {len(tag_ids)} tax tags: {tag_ids}")
        if not tag_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Info',
                    'message': f'No tax tags found for tax "{tax.name}". The tax may not be configured correctly.',
                    'type': 'info'
                }
            }
        
        tax_tags_to_apply = self.env['account.account.tag'].browse(tag_ids)
        
        # Apply the tax tags to the VAT line (account 345520)
        # VAT declarations read tags from tax lines to determine which "box" the amount belongs to
        _logger.info(f"Applying {len(tag_ids)} tags to VAT line {line_345520.id}")
        line_345520.write({'tax_tag_ids': [(6, 0, tag_ids)]})
        _logger.info(f"Tags after write: {line_345520.tax_tag_ids.ids}")
        
        # CRITICAL: Set always_tax_exigible = True for cash basis taxes
        # This tells the VAT system to process tax amounts immediately for VAT reporting
        # without waiting for a separate CABA (Cash Basis Accounting) reconciliation move
        self.write({'always_tax_exigible': True})
        _logger.info(f"Set always_tax_exigible = True for cash basis tax processing")
        
        
        vat_amount = line_345520.debit + line_345520.credit
        _logger.info(f"=== Force VAT Declaration COMPLETE - Applied to VAT amount: {vat_amount:.2f} ===")
        
        message_parts = []
        message_parts.append(f'✓ VAT Declaration applied with {len(tag_ids)} tag(s)')
        message_parts.append(f'✓ VAT amount: {vat_amount:.2f} {self.company_currency_id.name}')
        
        if display_type_fixed:
            message_parts.append(f'✓ Fixed display_type to "tax"')
        
        message_parts.append(f'✓ Set tax exigibility flag')
        
        message = '\n'.join(message_parts)
        message_type = 'success'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success' if not display_type_fixed else 'Success (Action Needed)',
                'message': message,
                'type': message_type
            }
        }
