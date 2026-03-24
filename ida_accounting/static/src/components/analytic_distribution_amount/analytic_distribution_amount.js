/** @odoo-module **/

import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";

/**
 * Patches AnalyticDistribution to add a two-way editable "Amount" column
 * in the analytic distribution popup.
 *
 * ─── Odoo 19 percentage convention ────────────────────────────────────────
 *   The virtual Record stores `percentage` in the 0–1 range (not 0–100).
 *     display amount  = baseAmount × percentage
 *     new percentage  = newAmount  / baseAmount   (clamped to [0, 1])
 *
 * ─── Why Math.round instead of toFixed ────────────────────────────────────
 *   IEEE 754 float multiplication can produce values like:
 *     3000 × 0.333333 = 999.99900000000003
 *   `.toFixed(2)` on that gives "999.99" instead of "1000.00" because the
 *   float is technically below the rounding threshold.
 *   `Math.round(raw × 100) / 100` avoids this by operating on the integer
 *   domain where float error is negligible for any realistic base amount.
 *
 * ─── OWL 2 event-handler rule ─────────────────────────────────────────────
 *   Always use  this.method(args)  in t-on-* expressions; bare method names
 *   are treated as free variables and lose the component's `this` binding.
 */
patch(AnalyticDistribution.prototype, {

    // ── Helpers ──────────────────────────────────────────────────────────────

    /**
     * Returns the monetary base for this record line (debit+credit or price_subtotal).
     * @returns {number}
     */
    _idaBaseAmount() {
        const d = this.props?.record?.data;
        if (!d) return 0;
        const fromJournal = (parseFloat(d.debit) || 0) + (parseFloat(d.credit) || 0);
        return fromJournal || Math.abs(parseFloat(d.price_subtotal) || 0);
    },

    /**
     * Returns the stable 2-decimal display amount for a distribution line.
     *
     * Uses Math.round(raw × 100) / 100 to avoid toFixed floating-point drift:
     *   - Input:  percentage 0–1, e.g. 0.333333
     *   - Output: e.g. "1000.00"  (string, always 2 decimal places)
     *
     * @param {number|string} percentage  0–1
     * @returns {string}
     */
    idaAmountValue(percentage) {
        const pct = parseFloat(percentage) || 0;
        const base = this._idaBaseAmount();
        const stable = Math.round(base * pct * 100) / 100;
        return stable.toFixed(2);
    },

    // ── Event handler ────────────────────────────────────────────────────────

    /**
     * Handles the "change" event on the Amount input.
     *
     * Rounds the entered amount to 2 decimal places, derives the new percentage
     * (0–1, full float precision — no artificial decimal cap), and writes it to
     * the virtual Record.  On re-render idaAmountValue() will recover the exact
     * 2-decimal amount thanks to Math.round.
     *
     * Must be invoked as  this.idaOnAmountChange(ev, data)  in OWL templates.
     *
     * @param {Event}  ev
     * @param {object} data  slot-scope from the popup's Record component
     */
    async idaOnAmountChange(ev, data) {
        const base = this._idaBaseAmount();
        if (!base) {
            ev.target.value = this.idaAmountValue(data?.record?.data?.percentage ?? 0);
            return;
        }

        const input = parseFloat(ev.target.value);
        if (isNaN(input) || input < 0) {
            ev.target.value = this.idaAmountValue(data?.record?.data?.percentage ?? 0);
            return;
        }

        // Clamp to monetary precision (2 decimal places) before deriving pct
        const newAmount = Math.round(input * 100) / 100;

        // Keep full float precision for pct — Math.round in idaAmountValue
        // guarantees a stable round-trip without any artificial cap here.
        const clamped = Math.min(1, Math.max(0, newAmount / base));

        if (!data?.record?.update) {
            console.warn("ida_accounting: data.record.update not available");
            return;
        }

        await data.record.update({ percentage: clamped });
    },
});
