/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Orderline } from "@point_of_sale/app/components/orderline/orderline";
import { useEffect } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { CustomDiscountLimitPopup } from "./discount_popup";
// Note: price check is handled at payment time in price_limit.js

patch(Orderline.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        // Debounce timer: prevents firing the popup on intermediate keystrokes
        // (e.g. typing "250" fires discount-change for "2", "25", "250").
        let _discountDebounceTimer = null;

        // ── Helpers ────────────────────────────────────────────────────────────
        const isProductScreen = () => this.pos.router.state.current === "ProductScreen";

        const isRefundOrder = () =>
            (this.pos.getOrder()?.getOrderlines() || []).some(l => l.getQuantity() < 0);

        const resetDiscount = (orderline) => {
            this.pos.numberBuffer.reset();
            orderline.setDiscount(0);
            this.pos.setDiscountFromUI(orderline, 0);
        };

        // ── Discount check ─────────────────────────────────────────────────────
        const checkDiscountLimit = async () => {
            if (!isProductScreen() || isRefundOrder()) return;
            if (!this.pos.config?.access_discount_limit) return;
            if (!this.props.line) return;

            // Only check when the cashier is actually in discount (%) mode
            // so that typing a price never triggers this popup.
            // pos.numpadMode values: "quantity" | "price" | "discount"
            if (this.pos.numpadMode !== 'discount') return;

            const orderline = this.pos.getOrder()?.getSelectedOrderline();
            const discount = parseFloat(this.props.line.discount || 0);
            const limit = parseFloat(this.pos.config.discount_limit || 0);

            if (discount <= limit || limit <= 0) return;

            this.dialog.add(CustomDiscountLimitPopup, {
                title: _t("Discount Limit Exceeded"),
                body: _t(
                    "The discount of %(discount)s% exceeds the allowed limit of %(limit)s%. Please enter supervisor PIN to approve.",
                    { discount: discount, limit: limit }
                ),
                confirm: async (password) => {
                    try {
                        const employee = await rpc("/pos/check_employee_pin", { pin: password });
                        if (employee && employee.discount_approval) {
                            this.notification.add(_t(`Discount approved by ${employee.name}`), { type: "success" });
                        } else if (employee && !employee.discount_approval) {
                            this.notification.add(_t("You do not have approval for this discount."), { type: "danger" });
                            if (orderline) resetDiscount(orderline);
                        } else {
                            this.notification.add(_t("Invalid employee PIN."), { type: "danger" });
                            if (orderline) resetDiscount(orderline);
                        }
                    } catch (err) {
                        console.error("RPC Error:", err);
                        this.notification.add(_t("Server error. Please try again."), { type: "danger" });
                        if (orderline) resetDiscount(orderline);
                    }
                },
                cancel: () => {
                    if (orderline) resetDiscount(orderline);
                },
            });
        };

        // Debounced wrapper: waits 650 ms after the last keystroke before
        // actually evaluating the discount.  This prevents the popup from
        // firing on intermediate values while the cashier is still typing
        // (e.g. typing "250" would otherwise trigger checks for "2" and "25").
        const checkDiscountLimitDebounced = () => {
            if (_discountDebounceTimer) {
                clearTimeout(_discountDebounceTimer);
            }
            _discountDebounceTimer = setTimeout(() => {
                _discountDebounceTimer = null;
                if (this.pos.config.access_discount_limit) {
                    checkDiscountLimit();
                }
            }, 650);
        };

        // ── Effects ────────────────────────────────────────────────────────────
        useEffect(
            () => { checkDiscountLimitDebounced(); },
            () => [this.props.line?.discount]
        );
    },
});