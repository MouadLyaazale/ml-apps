/** @odoo-module **/
/**
 * Display free-to-sell stock quantity on every POS product card.
 *
 * Strategy
 * --------
 * The PosStore service is created with `reactive(this)` in its constructor,
 * so every property we set on `this` inside setup() is part of the reactive
 * proxy that OWL components subscribe to.
 *
 * We patch PosStore.setup() to:
 *   1. Add `this.productStockQty = {}` (tracked reactive property)
 *   2. After the base setup completes, fetch stock from the server if
 *      `this.config.show_stock_qty` is enabled.
 *   3. Start a 60-second refresh timer.
 *
 * ProductCard reads `this.pos.productStockQty[pid]` in a getter called from
 * the template.  Because `this.pos` is the reactive PosStore proxy, OWL
 * tracks the property access and re-renders the card whenever stock changes.
 */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { rpc } from "@web/core/network/rpc";

// ── PosStore patch ────────────────────────────────────────────────────────────

patch(PosStore.prototype, {
    async setup(...args) {
        // Declare the stock dict BEFORE super.setup() so it is immediately part
        // of the reactive proxy. Components can safely read it at any time.
        this.productStockQty = {};
        await super.setup(...args);

        if (!this.config?.show_stock_qty) return;

        // Initial fetch right after the POS session is ready
        await this._fetchProductStock();

        // Periodic refresh every 60 s
        setInterval(() => this._fetchProductStock(), 60_000);
    },

    async _fetchProductStock() {
        try {
            const data = await rpc("/pos/product_stock", {
                config_id: this.config.id,
            });
            // Sync the reactive dict in-place so OWL detects the mutations.
            // - Delete keys that disappeared
            for (const key of Object.keys(this.productStockQty)) {
                if (!(key in data)) delete this.productStockQty[key];
            }
            // - Set / update existing keys
            for (const [key, val] of Object.entries(data)) {
                this.productStockQty[key] = val;
            }
        } catch (e) {
            console.warn("[pos_smart_discount_control] stock fetch error:", e);
        }
    },
});

// ── ProductCard patch ─────────────────────────────────────────────────────────

patch(ProductCard.prototype, {
    setup() {
        super.setup();
        try {
            this.pos = usePos();
        } catch {
            // Not inside the POS app context — feature unavailable
            this.pos = null;
        }
    },

    /**
     * Free-to-sell qty for this product, or null if:
     *   - feature is disabled on this POS config
     *   - product is not storable (not in the stock response)
     *
     * Accessing `this.pos.productStockQty[pid]` during OWL rendering
     * registers a reactive dependency — the card will automatically
     * re-render whenever that value is updated by `_fetchProductStock()`.
     */
    get stockQty() {
        if (!this.pos?.config?.show_stock_qty) return null;
        // Only show a badge for storable products
        if (!this.props.product?.is_storable) return null;
        const pid = String(this.props.productId);
        const qty = this.pos.productStockQty[pid];
        // If absent from dict the product has 0 quants (vacuumed by Odoo) → show 0
        return qty !== undefined ? qty : 0;
    },

    /** Bootstrap badge colour: red ≤ 0 | orange 1–5 | green > 5 */
    get stockBadgeClass() {
        const qty = this.stockQty;
        if (qty === null) return "";
        if (qty <= 0) return "bg-danger text-white";
        if (qty <= 5) return "bg-warning text-dark";
        return "bg-success text-white";
    },
});

