# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError


class InheritStockPicking(models.Model):
    _inherit ="stock.picking"

    @api.onchange('location_id')
    def _onchange_location_id_update_picking_type(self):
        """ Update picking type based on source location change. 
            User wants: Change location -> update picking type to match the new warehouse.
        """
        if not self.location_id:
            return

        # Find warehouse for this location
        warehouse = self.location_id.warehouse_id
        if not warehouse:
            # Try to find by lot_stock_id (default stock location for warehouse)
            warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', self.location_id.id)], limit=1)
        
        if not warehouse:
             # If still not found, try parent location's warehouse or search parent location in warehouses
             loc = self.location_id
             while loc and not warehouse:
                 warehouse = loc.warehouse_id
                 if not warehouse:
                     warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', loc.id)], limit=1)
                 loc = loc.location_id

        if warehouse:
            # Determine logic: We are changing source location. 
            # If current picking is outgoing (Delivery Order), we need an outgoing type from this warehouse.
            # If it's internal, we might want internal.
            # Default to the same code as current picking type, or 'outgoing' if not set.
            
            code = self.picking_type_id.code or 'outgoing'
            new_picking_type = self.env['stock.picking.type']
            
            # Prioritize default warehouse picking types to avoid selecting specialized ones (like PoS)
            if code == 'outgoing':
                new_picking_type = warehouse.out_type_id
            elif code == 'incoming':
                new_picking_type = warehouse.in_type_id
            elif code == 'internal':
                new_picking_type = warehouse.int_type_id
            
            # Fallback: Find a matching picking type in the new warehouse if default not set or code mismatch
            if not new_picking_type or new_picking_type.code != code:
                new_picking_type = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', warehouse.id),
                    ('code', '=', code)
                ], limit=1)
            
            if new_picking_type and new_picking_type != self.picking_type_id:
                current_location = self.location_id
                self.picking_type_id = new_picking_type.id
                # Setting picking_type_id might trigger standard onchange and reset location_id.
                # We restore location_id to ensure the user's selection is kept.
                if self.location_id != current_location:
                    self.location_id = current_location

    def _check_warehouse_restriction(self):
        """ Check if the user is allowed to perform actions on this picking based on warehouse restrictions. """
        if self.env.is_superuser() or self.env.user.has_group('base.group_system'):
            return True
            
        allowed_access = self.env.user.has_group('bi_warehouse_restrictions.group_restrict_operations')
        if not allowed_access:
            return True

        user = self.env.user
        
        # We only check restrictions if at least one restriction flag is active
        if not (user.restrict_operation or user.restrict_location or user.restrict_warehouse_list):
            return True
        
        # If user has access to create/write, we must iterate and check logic
        # OR logic: If user only has restrict_operation, check only operation
        # But wait, original code says:
        # if user.restrict_operation and user.restrict_location and user.restrict_warehouse_list:
        #    check (op OR loc OR wh)
        
        # Simpler check: If picking matches ANY allowed criterion, it is allowed.
        # UNLESS the user configured "AND" logic?
        # Looking at original search_fetch:
        # if all 3 set: domain += ['|','|', (op), (loc), (wh)] => OR logic.
        # So if picking matches op OR loc OR wh, it is allowed.
        
        allowed_ops = user.operation_ids.ids if user.restrict_operation else []
        allowed_locs = user.location_ids.ids if user.restrict_location else []
        allowed_whs = user.warehouse_ids.ids if user.restrict_warehouse_list else []
        
        for picking in self:
            is_allowed = False
            
            # Check Operation Type
            if user.restrict_operation:
                if picking.picking_type_id.id in allowed_ops:
                    is_allowed = True
            
            # Check Location
            if not is_allowed and user.restrict_location:
                if picking.location_id.id in allowed_locs:
                    is_allowed = True
                    
            # Check Warehouse
            if not is_allowed and user.restrict_warehouse_list:
                if picking.picking_type_id.warehouse_id.id in allowed_whs:
                    is_allowed = True
            
            # If no restrictions matched, user is denied.
            if not is_allowed:
                return False
        
        return True

    def write(self, vals):
        res = super(InheritStockPicking, self).write(vals)
        return res

    def button_validate(self):
        # Prevent validation if user doesn't have access
        if not self._check_warehouse_restriction():
            raise UserError(_("You do not have permission to validate transfers for this warehouse/operation type."))
        return super(InheritStockPicking, self).button_validate()

    def action_confirm(self):
        if not self._check_warehouse_restriction():
             raise UserError(_("You do not have permission to confirm transfers for this warehouse/operation type."))
        return super(InheritStockPicking, self).action_confirm()
        
    def action_assign(self):
        if not self._check_warehouse_restriction():
             raise UserError(_("You do not have permission to check availability for this warehouse/operation type."))
        return super(InheritStockPicking, self).action_assign()

    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        allowed_access = self.env.user.has_group('bi_warehouse_restrictions.group_restrict_operations')
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        
        extra_domain = []
        if allowed_access:
            conditions = []
            # Make sure we combine restrictions with OR if multiple are set
            # The logic is: User has access if (access via op) OR (access via loc) OR (access via wh) OR (is outgoing)
            
            if user.restrict_operation:
                conditions.append(('picking_type_id', 'in', user.operation_ids.ids))
            if user.restrict_location:
                conditions.append(('location_id', 'in', user.location_ids.ids))
            if user.restrict_warehouse_list:
                conditions.append(('picking_type_id.warehouse_id', 'in', user.warehouse_ids.ids))
            
            # Allow seeing all Outgoing / Delivery Orders
            conditions.append(('picking_type_code', '=', 'outgoing'))

            if conditions:
                # If using multiple conditions, join with OR
                if len(conditions) > 1:
                    extra_domain = ['|'] * (len(conditions) - 1) + conditions
                else:
                    extra_domain = conditions
        
        if extra_domain:
            domain += extra_domain

        return super(InheritStockPicking, self).search_fetch(domain, field_names, offset=0, limit=limit, order=None)

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        context = dict(self.env.context)
        allowed_access = self.env.user.has_group('bi_warehouse_restrictions.group_restrict_operations')
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        
        extra_domain = []
        if allowed_access:
            conditions = []
            
            if user.restrict_operation:
                conditions.append(('picking_type_id', 'in', user.operation_ids.ids))
            if user.restrict_location:
                conditions.append(('location_id', 'in', user.location_ids.ids))
            if user.restrict_warehouse_list:
                conditions.append(('picking_type_id.warehouse_id', 'in', user.warehouse_ids.ids))
            
            # Allow seeing all Outgoing / Delivery Orders
            conditions.append(('picking_type_code', '=', 'outgoing'))

            if conditions:
                if len(conditions) > 1:
                    extra_domain = ['|'] * (len(conditions) - 1) + conditions
                else:
                    extra_domain = conditions
        
        if extra_domain:
            domain += extra_domain

        return super(InheritStockPicking, self.sudo().with_context(context))._name_search(name, domain, operator, limit, order)
    
    

class InheritStockLocation(models.Model):
    _inherit="stock.location"
    
    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        domain = domain or []
        allowed_access = self.env.user.has_group('bi_warehouse_restrictions.group_restrict_operations')
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        final_location_ids = user.location_ids
    
        if user.restrict_location and allowed_access:
            domain += [('id','in',final_location_ids.ids)]
            
        return super(InheritStockLocation, self).search_fetch(domain, field_names, offset=0, limit=limit, order=None)

class InheritStockWarehouse(models.Model):
    _inherit="stock.warehouse"

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        domain = domain or []
        allowed_access = self.env.user.has_group('bi_warehouse_restrictions.group_restrict_operations')
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        final_warehouse_ids = user.warehouse_ids
    
        if user.restrict_warehouse_list and allowed_access:
            domain += [('id','in',final_warehouse_ids.ids)]

        return super(InheritStockWarehouse, self).search_fetch(domain, field_names, offset=0, limit=limit, order=None)

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        context = dict(self.env.context)
        domain = domain or []
        allowed_access = self.env.user.has_group('bi_warehouse_restrictions.group_restrict_operations')
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        final_warehouse_ids = user.warehouse_ids
    
        if user.restrict_warehouse_list and allowed_access:
            domain += [('id','in',final_warehouse_ids.ids)]

        return super(InheritStockWarehouse, self.sudo().with_context(context))._name_search(name, domain, operator, limit, order)
