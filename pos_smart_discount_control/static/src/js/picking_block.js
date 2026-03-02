/** @odoo-module **/
/**
 * Block the POS receipt (ticket) when a stock transfer is still pending.
 *
 * After order sync the server includes `failed_pickings` (a computed field on
 * pos.order) in the data returned to the frontend.  We hook into
 * OrderPaymentValidation.shouldHideValidationBehindFeedbackScreen() – which is
 * called right between finalizeValidation() (the sync) and the navigate() call
 * – to intercept the navigation and show an error dialog instead of the receipt
 * screen whenever any picking is still in a non-done state.
 */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";

patch(OrderPaymentValidation.prototype, {
    /**
     * Overridden to block navigation to ReceiptScreen when the POS order has
     * one or more unfinished stock transfers (`failed_pickings === true`).
     *
     * For the FeedbackScreen path we stay out of the way and delegate entirely
     * to the original implementation.
     */
    async shouldHideValidationBehindFeedbackScreen() {
        const nextPage = this.nextPage;

        // ── FeedbackScreen path ──────────────────────────────────────────────
        // Keep existing behaviour untouched (restaurant / feedback flow).
        if (nextPage.page === "FeedbackScreen") {
            return super.shouldHideValidationBehindFeedbackScreen(...arguments);
        }

        // ── Regular (ReceiptScreen) path ─────────────────────────────────────
        // Run finalizeValidation first so the order is synced to the server.
        // After this call, this.order.raw.failed_pickings reflects the server
        // value (computed on pos.order and included by _load_pos_data_fields).
        let response;
        try {
            this.pos.env.services.ui.block();
            response = await this.finalizeValidation();
            if (response && response.name === "RPCError") {
                return false;
            }
        } finally {
            this.pos.env.services.ui.unblock();
        }

        // ── Block receipt when any picking is still pending ──────────────────
        if (this.order.raw?.failed_pickings) {
            await this.pos.dialog.add(AlertDialog, {
                title: _t("Transfert en attente"),
                body: _t(
                    "Le ticket ne peut pas être imprimé car un ou plusieurs " +
                    "transferts de stock ne sont pas encore validés. " +
                    "Veuillez valider la livraison puis rouvrir la commande " +
                    "pour imprimer le ticket."
                ),
            });
            // Navigate back to the product screen instead of the receipt.
            this.pos.navigate("ProductScreen");
            return;
        }

        // ── Normal flow: navigate to ReceiptScreen ───────────────────────────
        this.pos.navigate(nextPage.page, nextPage.params);
    },
});
