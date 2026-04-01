/** @odoo-module **/

import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";

/**
 * Patches AnalyticDistribution to add a two-way editable "Amount" column.
 *
 * ── Root cause of decimal drift ───────────────────────────────────────────
 *   After idaOnAmountChange calls this.save(), Odoo's server-side onchange
 *   normalises the analytic distribution percentages to `analytic_precision`
 *   decimal places (default = 2).  On the subsequent re-render the rounded
 *   percentage is used to recompute the displayed amount, causing drift:
 *
 *     entered  333.33  →  stored as  33.333 %
 *     server rounds   →  33.33 %
 *     re-render       →  1 000 × 0.3333 = 333.30  ✗
 *
 * ── Fix ───────────────────────────────────────────────────────────────────
 *   Maintain a reactive amount cache (_idaAmounts) keyed by analytic account
 *   id.  idaAmountDisplay() returns the cached string when available, so the
 *   displayed amount is always the one the user actually entered — regardless
 *   of what the server returns.  The cache is per component instance, so it
 *   resets whenever the popup is closed and reopened.
 *
 * ── Why type="text" on the input ──────────────────────────────────────────
 *   <input type="number"> strips trailing zeros:
 *     setAttribute('value', '500.00')  →  shows "500"  ✗
 *   type="text" + inputmode="decimal"  →  preserves "500.00"  ✓
 *
 * ── OWL 2 binding rule ────────────────────────────────────────────────────
 *   Always write  this.method(args)  in t-on-* arrow functions; bare names
 *   are free variables and lose the component's `this`.
 */
patch(AnalyticDistribution.prototype, {

    setup() {
        super.setup?.();
        // Reactive map: analytic account id (string) → amount string "333.33"
        // Keeps the displayed amount stable after server-side rounding.
        this._idaAmounts = useState({});
    },

    // ── Helpers ──────────────────────────────────────────────────────────────

    _idaBaseAmount() {
        const d = this.props?.record?.data;
        if (!d) return 0;
        const fromJournal = (parseFloat(d.debit) || 0) + (parseFloat(d.credit) || 0);
        return fromJournal || Math.abs(parseFloat(d.price_subtotal) || 0);
    },

    /**
     * Converts a 0–1 percentage to a stable 2-decimal string.
     * Math.round(raw × 100) / 100 is used instead of toFixed to avoid
     * IEEE 754 rounding errors (e.g. 3000 × 0.333333 = 999.999…03).
     */
    idaAmountValue(percentage) {
        const pct = parseFloat(percentage) || 0;
        const base = this._idaBaseAmount();
        return (Math.round(base * pct * 100) / 100).toFixed(2);
    },

    /**
     * Returns the amount to display for `line`.
     * Prefers the cached value set by idaOnAmountChange so the display
     * never drifts due to server-side percentage rounding.
     */
    idaAmountDisplay(line) {
        return this._idaAmounts[line.id] ?? this.idaAmountValue(line.percentage);
    },

    // ── Event handler ────────────────────────────────────────────────────────

    async idaOnAmountChange(ev, line) {
        const base = this._idaBaseAmount();
        if (!base) {
            ev.target.value = this.idaAmountDisplay(line);
            return;
        }

        const input = parseFloat(ev.target.value);
        if (isNaN(input) || input < 0) {
            ev.target.value = this.idaAmountDisplay(line);
            return;
        }

        const newAmount = Math.round(input * 100) / 100;
        const clamped = Math.min(1, Math.max(0, newAmount / base));

        // Cache the amount BEFORE save so every re-render shows the user's value.
        this._idaAmounts[line.id] = newAmount.toFixed(2);

        // Update the reactive percentage (keeps the % column in sync).
        line.percentage = clamped;

        if (typeof this.save === "function") await this.save();

        ev.target.value = newAmount.toFixed(2);
    },
});
