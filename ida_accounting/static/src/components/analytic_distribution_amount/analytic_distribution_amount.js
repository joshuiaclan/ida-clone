/** @odoo-module **/

import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";

/**
 * Patches AnalyticDistribution to support a two-way editable "Amount" column
 * inside the analytic distribution popup.
 *
 * Percentage storage in Odoo 19 popup virtual records is 0–100 (e.g. 50 = 50 %).
 * Amount  = baseAmount × (percentage / 100)
 * Reverse = percentage = (amount / baseAmount) × 100
 *
 * Base amount resolution (first non-zero wins):
 *   1. debit + credit     → account.move.line on the Journal Items tab
 *   2. price_subtotal     → invoice / SO lines
 */
patch(AnalyticDistribution.prototype, {

    // ── helpers ──────────────────────────────────────────────────────────────

    /** Returns the monetary base for this journal/invoice line. */
    _idaBaseAmount() {
        const d = this.props.record?.data;
        if (!d) return 0;
        const fromJournal = (d.debit ?? 0) + (d.credit ?? 0);
        return fromJournal || Math.abs(d.price_subtotal ?? 0);
    },

    /**
     * Computes the distribution amount from a percentage.
     * @param {number|string} percentage  0–100
     * @returns {number}
     */
    _idaAmountFromPct(percentage) {
        const pct = parseFloat(percentage) || 0;
        return this._idaBaseAmount() * (pct / 100);
    },

    /**
     * Formats the amount for display inside the input.
     * @param {number|string} percentage  0–100
     * @returns {string}  e.g. "1250.00"
     */
    idaAmountValue(percentage) {
        return this._idaAmountFromPct(percentage).toFixed(2);
    },

    // ── event handlers ───────────────────────────────────────────────────────

    /**
     * Called when the user edits the Amount input.
     * Converts the entered amount back to a percentage and writes it to the
     * virtual distribution record so Odoo reacts normally.
     *
     * @param {InputEvent} ev
     * @param {object}     data  — template context `data` from the popup loop
     */
    async idaOnAmountInput(ev, data) {
        const base = this._idaBaseAmount();
        if (!base) return;

        const newAmount = parseFloat(ev.target.value);
        if (isNaN(newAmount)) return;

        // Clamp: percentage must stay within 0–100 range
        const newPct = Math.min(100, Math.max(0, (newAmount / base) * 100));
        await data.record.update({ percentage: parseFloat(newPct.toFixed(4)) });
    },
});
