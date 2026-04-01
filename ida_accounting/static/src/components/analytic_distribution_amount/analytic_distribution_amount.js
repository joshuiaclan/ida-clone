/** @odoo-module **/

import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";

/**
 * Patches AnalyticDistribution to add a two-way editable "Amount" column
 * backed by a persistent backend field `analytic_distribution_amounts`.
 *
 * The field stores { analytic_account_id: amount } as a JSON blob on
 * account.move.line so the user's entered amounts survive saves, reloads,
 * and server-side percentage normalisation without ever drifting.
 *
 * Display priority:
 *   1. analytic_distribution_amounts[line.id]  — the persisted amount
 *   2. Computed from line.percentage × base     — fallback for new lines
 *
 * On change:
 *   • line.percentage is updated (keeps the % column in sync)
 *   • analytic_distribution_amounts is updated on the record via record.update()
 *   • this.save() serialises the new percentage to the parent record
 */
patch(AnalyticDistribution.prototype, {

    // ── Helpers ──────────────────────────────────────────────────────────────

    _idaBaseAmount() {
        const d = this.props?.record?.data;
        if (!d) return 0;
        const fromJournal = (parseFloat(d.debit) || 0) + (parseFloat(d.credit) || 0);
        return fromJournal || Math.abs(parseFloat(d.price_subtotal) || 0);
    },

    /**
     * Returns the display string for the Amount column for `line`.
     *
     * Reads from `analytic_distribution_amounts` on the parent record first.
     * Falls back to computing from the stored percentage only when no
     * persisted amount exists (e.g. first time the popup is opened on a line
     * whose analytic distribution was set via the % input, not the Amount input).
     */
    idaAmountDisplay(line) {
        const saved = this.props?.record?.data?.analytic_distribution_amounts;
        if (saved && line.id in saved) {
            return parseFloat(saved[line.id]).toFixed(2);
        }
        // Fallback: compute from percentage
        const pct = parseFloat(line.percentage) || 0;
        const base = this._idaBaseAmount();
        return (Math.round(base * pct * 100) / 100).toFixed(2);
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

        // 1. Update the percentage on the reactive state (keeps % column in sync).
        line.percentage = clamped;

        // 2. Persist the exact entered amount to the backend field so it
        //    survives server-side percentage rounding on save/reload.
        const currentAmounts = Object.assign(
            {},
            this.props?.record?.data?.analytic_distribution_amounts || {}
        );
        currentAmounts[line.id] = newAmount;
        await this.props.record.update({ analytic_distribution_amounts: currentAmounts });

        // 3. Serialise the new percentage to the analytic_distribution field.
        if (typeof this.save === "function") await this.save();

        ev.target.value = newAmount.toFixed(2);
    },
});
