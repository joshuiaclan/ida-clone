/** @odoo-module **/

import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";

/**
 * Patches AnalyticDistribution to add a two-way editable "Amount" column
 * in the analytic distribution popup.
 *
 * ── Why we bypass lineChanged ──────────────────────────────────────────────
 *   Odoo 19's lineChanged() rounds the percentage to
 *   `analytic_precision + 2` decimal places (default analytic_precision = 2,
 *   so 4 decimal places in 0–1 range).
 *
 *   Rounding precision in 0–1 range = 0.0001
 *   → minimum amount step                = base × 0.0001
 *   → for base = 1 000                   = 0.10   (cents are lost!)
 *   → for base = 10 000                  = 1.00
 *
 *   By writing `line.percentage` directly on the reactive state object we
 *   keep full float64 precision.  Calling this.save() then serialises via
 *   dataToJson (×100) and the server stores e.g. "33.333" in the JSON field.
 *   On reload jsonToData divides by 100, recovering 0.33333 exactly.
 *
 * ── Why type="text" on the input ──────────────────────────────────────────
 *   <input type="number"> strips trailing zeros:
 *     setAttribute('value', '500.00')  →  browser displays "500"  ✗
 *   <input type="text" inputmode="decimal">  preserves "500.00"   ✓
 *
 * ── Why Math.round(x × 100) / 100 instead of toFixed ─────────────────────
 *   IEEE 754 multiplication can yield e.g. 3000 × 0.333333 = 999.9990000…03.
 *   .toFixed(2) can round that DOWN to "999.99"; Math.round operates in the
 *   integer domain where the error is negligible and always rounds correctly.
 *
 * ── OWL 2 binding rule ────────────────────────────────────────────────────
 *   In t-on-* arrow-function expressions bare names are free variables —
 *   use  this.method(args)  to call it as a bound component method.
 */
patch(AnalyticDistribution.prototype, {

    // ── Helpers ──────────────────────────────────────────────────────────────

    /**
     * Returns the monetary base for this record line.
     * Priority: debit + credit (journal items) → |price_subtotal| (invoice lines).
     * @returns {number}
     */
    _idaBaseAmount() {
        const d = this.props?.record?.data;
        if (!d) return 0;
        const fromJournal = (parseFloat(d.debit) || 0) + (parseFloat(d.credit) || 0);
        return fromJournal || Math.abs(parseFloat(d.price_subtotal) || 0);
    },

    /**
     * Converts a 0–1 percentage to a stable 2-decimal display string.
     *
     * Uses Math.round(raw × 100) / 100 to avoid toFixed floating-point drift.
     * Returns a string so <input type="text"> shows exactly two decimal places
     * (e.g. "500.00", not "500").
     *
     * Called from t-att-value — OWL evaluates t-att-* with the component as
     * `this`, so the method always has the correct context.
     *
     * @param {number|string} percentage  0–1 (Odoo 19 internal representation)
     * @returns {string}  e.g. "333.33"
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
     * Writes the new percentage directly to the reactive `line` object from
     * state.formattedData, bypassing lineChanged() and its precision rounding.
     * Then calls this.save() which runs dataToJson() (×100) and updates the
     * parent record — full float64 precision is preserved through the cycle.
     *
     * Must be called as  this.idaOnAmountChange(ev, line)  in OWL templates.
     *
     * @param {Event}  ev    DOM change event from the Amount <input>.
     * @param {object} line  Reactive entry from this.state.formattedData.
     */
    async idaOnAmountChange(ev, line) {
        const base = this._idaBaseAmount();
        if (!base) {
            ev.target.value = this.idaAmountValue(line?.percentage ?? 0);
            return;
        }

        const input = parseFloat(ev.target.value);
        if (isNaN(input) || input < 0) {
            ev.target.value = this.idaAmountValue(line?.percentage ?? 0);
            return;
        }

        // Normalise to monetary precision (2 dp) before deriving pct
        const newAmount = Math.round(input * 100) / 100;

        // Full float precision — no artificial cap.
        // Math.round in idaAmountValue guarantees a stable round-trip.
        const clamped = Math.min(1, Math.max(0, newAmount / base));

        // ── Key fix ────────────────────────────────────────────────────────
        // Write directly to the reactive state object, bypassing lineChanged()
        // which would round to only analytic_precision+2 decimal places (4 by
        // default) — too coarse for 2-dp amounts when base > 100.
        line.percentage = clamped;

        // Persist: dataToJson() serialises (clamped × 100) → the server stores
        // e.g. "33.333"; jsonToData on reload divides by 100 → 0.33333 exactly.
        if (typeof this.save === "function") {
            await this.save();
        }

        // Lock the displayed value after any OWL re-render triggered by save().
        // Without this, t-att-value could overwrite the input with a
        // slightly different float string.
        ev.target.value = newAmount.toFixed(2);
    },
});
