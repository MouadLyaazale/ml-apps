/** @odoo-module **/
/**
 * Safety-net: block payment if any orderline's price is below the configured
 * minimum price percentage of the product's sale price (lst_price).
 */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { CustomDiscountLimitPopup } from "./discount_popup";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this._priceDialog = useService("dialog");
        this._priceNotif = useService("notification");
        this._posStore = usePos();
    },

    async validateOrder(isForceValidate) {
        if (this._posStore.config?.access_price_limit) {
            const blocked = await this._checkAllLinePrices();
            if (blocked) return;   // stay on PaymentScreen
        }
        return super.validateOrder(isForceValidate);
    },

    /**
     * Walk every orderline, find any that breach the min-price rule.
     *
     * The check uses the EFFECTIVE unit price, i.e. price_unit after applying
     * the line's discount percentage:
     *
     *   effectivePrice = price_unit × (1 − discount / 100)
     *
     * This means a cashier cannot bypass the limit by combining a small price
     * change with a large discount (or vice-versa).
     *
     * The "price_limit" config value (e.g. 15) means:
     *   → minimum allowed effective price = 15% of the product's sale price
     *   → setting 80 means the cashier cannot sell below 80% of list price
     *
     * Returns true if payment should be blocked (unapproved breach found).
     */
    async _checkAllLinePrices() {
        const config = this._posStore.config;
        const limitPct = parseFloat(config?.price_limit || 0);
        if (limitPct <= 0) return false;

        const order = this._posStore.getOrder();
        if (!order) return false;

        for (const line of order.getOrderlines()) {
            const unitPrice = parseFloat(line.price_unit || 0);
            if (unitPrice <= 0) continue;

            // Factor in the line discount to get the real price the customer pays
            const discountPct = parseFloat(line.discount || 0);
            const effectivePrice = unitPrice * (1 - discountPct / 100);

            const product = line.product_id || line.product;
            const lstPrice =
                parseFloat(product?.lst_price) ||
                parseFloat(product?.price) ||
                0;

            if (lstPrice <= 0) continue;

            // minPrice = e.g. 15% of sale price
            const minPrice = lstPrice * (limitPct / 100);
            if (effectivePrice >= minPrice) continue;

            // This line breaches the limit — ask for PIN
            const approved = await this._askPriceApproval(line, effectivePrice, discountPct, unitPrice, minPrice, lstPrice, limitPct);
            if (!approved) return true;   // block payment
        }
        return false;
    },

    _askPriceApproval(line, effectivePrice, discountPct, unitPrice, minPrice, lstPrice, limitPct) {
        return new Promise((resolve) => {
            // Build a human-readable explanation of what triggered the block
            const discountInfo = discountPct > 0
                ? _t(" (prix %(unit)s DH − remise %(disc)s%%)", { unit: unitPrice.toFixed(2), disc: discountPct })
                : "";
            this._priceDialog.add(CustomDiscountLimitPopup, {
                title: _t("Prix en dessous du minimum autorisé"),
                body: _t(
                    "Ligne « %(prod)s » : prix effectif %(price)s DH%(disc_info)s < minimum %(min)s DH (%(pct)s%% de %(lst)s DH). Entrez le code PIN superviseur.",
                    {
                        prod: (line.product_id || line.product)?.display_name || "",
                        price: effectivePrice.toFixed(2),
                        disc_info: discountInfo,
                        min: minPrice.toFixed(2),
                        pct: limitPct,
                        lst: lstPrice.toFixed(2),
                    }
                ),
                confirm: async (pin) => {
                    try {
                        const employee = await rpc("/pos/check_employee_pin", { pin });
                        if (employee && employee.price_approval) {
                            this._priceNotif.add(
                                _t(`Prix approuvé par ${employee.name}`),
                                { type: "success" }
                            );
                            resolve(true);
                        } else if (employee) {
                            this._priceNotif.add(
                                _t("Pas d'autorisation pour modifier le prix."),
                                { type: "danger" }
                            );
                            resolve(false);
                        } else {
                            this._priceNotif.add(_t("PIN invalide."), { type: "danger" });
                            resolve(false);
                        }
                    } catch {
                        this._priceNotif.add(_t("Erreur serveur."), { type: "danger" });
                        resolve(false);
                    }
                },
                cancel: () => resolve(false),
                close: () => {},
            });
        });
    },
});
