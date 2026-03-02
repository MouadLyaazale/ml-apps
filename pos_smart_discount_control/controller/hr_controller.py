# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http  
from odoo.http import request  


class EmployeePinController(http.Controller):

    @http.route('/pos/product_stock', type='jsonrpc', auth='user')
    def get_product_stock(self, config_id):
        """
        Returns {product_id: free_qty} for every storable product,
        filtered to the internal stock location of the POS config's warehouse.
        free_qty = qty_on_hand - qty_reserved
        """
        config = request.env['pos.config'].sudo().browse(config_id)
        if not config.exists() or not config.show_stock_qty:
            return {}

        # Get the warehouse's main stock location
        warehouse = config.picking_type_id.warehouse_id or config.warehouse_id
        if not warehouse:
            return {}
        location = warehouse.lot_stock_id
        if not location:
            return {}

        # Fetch all child locations (internal) under the warehouse stock location
        all_locations = request.env['stock.location'].sudo().search([
            ('id', 'child_of', location.id),
            ('usage', '=', 'internal'),
        ])
        location_ids = all_locations.ids or [location.id]

        # Aggregate quants by product.product first, then map to template IDs.
        # ProductCard in POS JS receives product.template id (not variant id).
        quants = request.env['stock.quant'].sudo().read_group(
            domain=[
                ('location_id', 'in', location_ids),
                ('product_id.is_storable', '=', True),
            ],
            fields=['product_id', 'quantity:sum', 'reserved_quantity:sum'],
            groupby=['product_id'],
        )

        # Build product.product → product.template mapping
        product_ids = [q['product_id'][0] for q in quants]
        products = request.env['product.product'].sudo().browse(product_ids)
        tmpl_map = {p.id: p.product_tmpl_id.id for p in products}

        # Sum free qty per template (multiple variants → same template)
        result = {}
        for q in quants:
            prod_id = q['product_id'][0]
            tmpl_id = tmpl_map.get(prod_id)
            if not tmpl_id:
                continue
            free = (q['quantity'] or 0.0) - (q['reserved_quantity'] or 0.0)
            key = str(tmpl_id)
            result[key] = round(result.get(key, 0.0) + free, 3)

        # Clamp negatives to 0 (over-reserved products should show 0, not negative)
        result = {k: max(0.0, v) for k, v in result.items()}

        return result

    @http.route('/pos/bl_a4/<int:order_id>', type='http', auth='user')
    def print_bl_a4(self, order_id, **kwargs):
        """
        Generate and download the A4 Bon de Livraison PDF for a POS order.

        Finds the stock.picking(s) linked to the POS order and renders the
        DOCX template configured on the POS config (bl_docx_template_id).
        After generation, redirects the browser to the ir.attachment download
        URL so the PDF opens / downloads in the new tab.
        """
        import werkzeug

        order = request.env['pos.order'].sudo().browse(order_id)
        if not order.exists():
            return request.not_found()

        config = order.config_id
        if not config.show_bl_a4:
            return request.make_response('BL A4 printing is not enabled for this POS.', status=403)

        pickings = order.picking_ids
        if not pickings:
            return request.make_response(
                '<html><body><p>No delivery order found for this POS order.</p></body></html>',
                headers=[('Content-Type', 'text/html')],
                status=404,
            )

        template_id = config.bl_docx_template_id or 1
        template = request.env['docx.template'].sudo().browse(template_id)
        if not template.exists():
            return request.make_response(
                f'<html><body><p>DOCX Template (id={template_id}) not found.</p></body></html>',
                headers=[('Content-Type', 'text/html')],
                status=404,
            )

        result = template.with_context(
            active_ids=pickings.ids,
            active_model='stock.picking',
            menu_action_id=template_id,
        ).make_docx_pdf_report()

        if result and result.get('type') == 'ir.actions.act_url':
            return werkzeug.utils.redirect(result['url'])

        return request.make_response(
            '<html><body><p>Report generation failed.</p></body></html>',
            headers=[('Content-Type', 'text/html')],
            status=500,
        )

    @http.route('/pos/check_employee_pin', type='jsonrpc', auth='public')
    def check_employee_pin(self, pin):

        matching_employees = request.env['hr.employee'].sudo().search([('pin', '=', pin)])
        for emp in matching_employees:
            return {
                'id': emp.id,
                'name': emp.name,
                'discount_approval': emp.discount_approval,
                'price_approval': emp.price_approval,
            }
