/** @odoo-module **/

import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";

/**
 * Patches AnalyticDistribution to add a two-way editable "Amount" column
 * in the analytic distribution popup.
 *
 * ─── Odoo 19 percentage convention ────────────────────────────────────────
 *   The virtual Record stores `percentage` in the 0–1 range (not 0–100).
 *   Therefore:
 *     display amount  = baseAmount × percentage          (no extra ÷ 100)
 *     new percentage  = newAmount  / baseAmount          (result in 0–1)
 *
 * ─── OWL 2 event-handler rule ─────────────────────────────────────────────
 *   Always call patched methods with "this." inside t-on-* expressions so
 *   OWL binds the call to the component instance:
 *     ✗  t-on-change="(ev) => idaOnAmountChange(ev, data)"   → this = undefined
 *     ✓  t-on-change="(ev) => this.idaOnAmountChange(ev, data)"
 *
 * ─── Base-amount resolution (first non-zero wins) ─────────────────────────
 *   1. debit + credit    → account.move.line (Journal Items tab)
 *   2. price_subtotal    → invoice / SO lines
 */
patch(AnalyticDistribution.prototype, {

    // ── Helpers ──────────────────────────────────────────────────────────────

    /**
     * Returns the monetary base for this record line.
     * Reads from props.record (the parent account.move.line / sale.order.line).
     * Returns 0 when unavailable so callers can bail out gracefully.
     *
     * @returns {number}
     */
    _idaBaseAmount() {
        const d = this.props?.record?.data;
        if (!d) return 0;
        const fromJournal = (parseFloat(d.debit) || 0) + (parseFloat(d.credit) || 0);
        if (fromJournal) return fromJournal;
        return Math.abs(parseFloat(d.price_subtotal) || 0);
    },

    /**
     * Computes the display amount for a distribution line.
     * Called from t-att-value in the template (OWL evaluates t-att-* with
     * the component as `this`, so this method always has the right context).
     *
     * @param {number|string} percentage  0–1  (Odoo 19 internal representation)
     * @returns {number}
     */
    idaAmountValue(percentage) {
        const pct = parseFloat(percentage) || 0;
        const base = this._idaBaseAmount();
        return parseFloat((base * pct).toFixed(2));
    },

    // ── Event handler ────────────────────────────────────────────────────────

    /**
     * Handles the "change" event on the Amount input.
     *
     * Calculates the new percentage (0–1) from the entered amount and writes it
     * to the virtual distribution record via data.record.update().  Odoo's own
     * onRecordChanged → lineChanged flow then persists the full analytic JSON.
     *
     * IMPORTANT: must be called as  this.idaOnAmountChange(ev, data)  inside the
     * OWL template so that `this` is bound to the AnalyticDistribution instance.
     *
     * @param {Event}  ev    The DOM change event from the amount <input>.
     * @param {object} data  Slot-scope from the Record component in the popup.
     */
    async idaOnAmountChange(ev, data) {
        const base = this._idaBaseAmount();
        if (!base) {
            // No base amount available – restore the displayed value and bail.
            ev.target.value = this.idaAmountValue(data?.record?.data?.percentage ?? 0);
            return;
        }

        const newAmount = parseFloat(ev.target.value);
        if (isNaN(newAmount) || newAmount < 0) {
            // Invalid input – reset to the current computed amount.
            ev.target.value = this.idaAmountValue(data?.record?.data?.percentage ?? 0);
            return;
        }

        // Clamp to [0, 1] and round to sufficient precision for Odoo.
        const rawPct = newAmount / base;
        const clampedPct = Math.min(1, Math.max(0, rawPct));
        const rounded = parseFloat(clampedPct.toFixed(6));

        if (!data?.record?.update) {
            console.warn("ida_accounting: data.record.update not available");
            return;
        }

        await data.record.update({ percentage: rounded });
    },
});
