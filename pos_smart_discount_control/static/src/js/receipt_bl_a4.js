/** @odoo-module **/
/**
 * Add an "Imprimer BL (A4)" button to the POS receipt screen.
 *
 * Clicking the button opens /pos/bl_a4/<order_id> in a new browser tab.
 * The backend controller generates the DOCX/PDF report using the template
 * configured in POS settings (bl_docx_template_id) and redirects to the
 * ir.attachment download URL.
 *
 * The button is only rendered when:
 *   - pos.config.show_bl_a4 is true
 *   - the current order has a server-side ID (i.e. has been synced)
 */

import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";

patch(ReceiptScreen.prototype, {
    /**
     * Open the A4 BL PDF in a new tab.
     * The controller /pos/bl_a4/<id> handles the DOCX → PDF generation and
     * redirects the browser to the ir.attachment download.
     */
    printBLA4() {
        const order = this.currentOrder;
        if (!order?.id) return;
        window.open(`/pos/bl_a4/${order.id}`, "_blank");
    },
});
