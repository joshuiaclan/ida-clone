/** @odoo-module **/

import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";

/**
 * Patches AnalyticDistribution to add a two-way editable "Amount" column
 * in the analytic distribution popup.
 *
 * IMPORTANT — Odoo 19 stores percentage in 0–1 range internally
 * (see jsonToData: `percentage: percentage / 100`).
 * Therefore:
 *   amount  = baseAmount × percentage          (NO extra ÷100)
 *   reverse = newPct    = newAmount / baseAmount  (result is 0–1)
 *
 * Base amount resolution (first non-zero wins):
 *   1. debit + credit    → account.move.line (Journal Items tab)
 *   2. price_subtotal    → invoice / SO lines
 */
patch(AnalyticDistribution.prototype, {

    // ─── helpers ─────────────────────────────────────────────────────────────

    /** Returns the monetary base amount for this record line. */
    _idaBaseAmount() {
        const d = this.props.record?.data;
        if (!d) return 0;
        const fromJournal = (d.debit ?? 0) + (d.credit ?? 0);
        return fromJournal || Math.abs(d.price_subtotal ?? 0);
    },

    /**
     * Returns the numeric amount for a distribution line.
     * @param {number} percentage  0–1  (Odoo 19 internal representation)
     * @returns {number}
     */
    idaAmountValue(percentage) {
        const pct = parseFloat(percentage) || 0;
        const amount = this._idaBaseAmount() * pct;
        return parseFloat(amount.toFixed(2));
    },

    // ─── event handler ───────────────────────────────────────────────────────

    /**
     * Called when the user edits the Amount input (on blur / Enter).
     * Calculates the new percentage (0–1) and writes it to the virtual
     * distribution record; Odoo's own onRecordChanged → lineChanged flow
     * then saves the full analytic distribution.
     *
     * @param {Event}  ev
     * @param {object} data  slot-scope from the Record component inside the popup
     */
    async idaOnAmountChange(ev, data) {
        const base = this._idaBaseAmount();
        if (!base) return;

        const newAmount = parseFloat(ev.target.value);
        if (isNaN(newAmount) || newAmount < 0) return;

        // Result must stay in 0–1 (clamp to valid range)
        const newPct = Math.min(1, Math.max(0, newAmount / base));

        // Round to the same precision Odoo uses internally (+2 over display digits)
        const digits = this.decimalPrecision?.digits?.[1] ?? 2;
        const rounded = parseFloat(newPct.toFixed(digits + 2));

        await data.record.update({ percentage: rounded });
    },
});
