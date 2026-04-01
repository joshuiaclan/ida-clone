/** @odoo-module **/

import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";

/**
 * Session-level fallback cache so the correct amount is shown even if the
 * backend field hasn't been loaded into record.data yet.
 * Key: "<resId>|<analyticAccountId>"  Value: amount string e.g. "425.00"
 */
const _idaAmountCache = new Map();

patch(AnalyticDistribution.prototype, {

    // ── Helpers ──────────────────────────────────────────────────────────────

    _idaBaseAmount() {
        const d = this.props?.record?.data;
        if (!d) return 0;
        const fromJournal = (parseFloat(d.debit) || 0) + (parseFloat(d.credit) || 0);
        return fromJournal || Math.abs(parseFloat(d.price_subtotal) || 0);
    },

    _idaCacheKey(line) {
        const resId = this.props?.record?.resId ?? "new";
        return `${resId}|${line.id}`;
    },

    /**
     * Amount to display for a distribution line.
     *
     * Priority:
     *   1. analytic_distribution_amounts backend field (persists across sessions)
     *   2. Module-level session cache (survives popup close/open within the tab)
     *   3. Computed from percentage × base (always available, may drift)
     *
     * For 1 and 2 the stored amount is only used when it is still consistent
     * with the current line.percentage — i.e. the user has not manually changed
     * the percentage since the amount was last set.  A mismatch means the
     * percentage was edited independently, so we fall through to the computed
     * value so the amount updates in sync with the new percentage.
     *
     * Tolerance of 0.00005 (0.005 %) covers server-side rounding of the stored
     * percentage to two decimal places without accidentally accepting a genuine
     * manual percentage change.
     */
    idaAmountDisplay(line) {
        const base = this._idaBaseAmount();
        const pct = parseFloat(line.percentage) || 0;
        const computed = (Math.round(base * pct * 100) / 100).toFixed(2);

        if (!base) return computed;

        const isConsistent = (storedAmount) => {
            const amount = parseFloat(storedAmount);
            if (isNaN(amount)) return false;
            return Math.abs(amount / base - pct) < 0.00005;
        };

        // 1. Backend field
        const saved = this.props?.record?.data?.analytic_distribution_amounts;
        if (saved) {
            const key = String(line.id);
            if (key in saved) {
                return isConsistent(saved[key])
                    ? parseFloat(saved[key]).toFixed(2)
                    : computed;
            }
        }

        // 2. Session cache
        const cacheKey = this._idaCacheKey(line);
        if (_idaAmountCache.has(cacheKey)) {
            const cached = _idaAmountCache.get(cacheKey);
            if (isConsistent(cached)) return cached;
            // Stale — percentage changed manually, discard
            _idaAmountCache.delete(cacheKey);
        }

        // 3. Computed fallback
        return computed;
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
        const amountStr = newAmount.toFixed(2);
        const pctDisplay = (Math.round(clamped * 10000) / 100).toFixed(2);

        // Write to session cache immediately so idaAmountDisplay returns the
        // correct value even before the backend field is confirmed saved.
        _idaAmountCache.set(this._idaCacheKey(line), amountStr);

        // Update the percentage in reactive state (keeps % column in sync).
        line.percentage = clamped;

        // Directly update the percentage input in the same row so it reflects
        // the new value immediately, regardless of OWL's render cycle.
        // We find every input in the row that is NOT our amount input and
        // pick the one that currently holds a number that looks like a percentage
        // (between 0 and 100), as that is the percentage column.
        const row = ev.target.closest("tr");
        if (row) {
            const siblings = Array.from(row.querySelectorAll("input")).filter(
                (el) => el !== ev.target
            );
            const pctInput = siblings.find((el) => {
                const v = parseFloat(el.value);
                return !isNaN(v) && v >= 0 && v <= 100;
            });
            if (pctInput) pctInput.value = pctDisplay;
        }

        // ── ORDERING IS CRITICAL ────────────────────────────────────────────
        // 1. Save the percentage FIRST.
        //    this.save() serialises state.formattedData (which includes our
        //    mutated line.percentage) into analytic_distribution and calls
        //    record.update(). If we called record.update() for the amounts
        //    field first, onWillUpdateProps would reinitialise formattedData
        //    from the old analytic_distribution, overwriting line.percentage
        //    before this.save() could read it — causing drift.
        if (typeof this.save === "function") {
            await this.save();
        }

        // 2. Then persist the exact entered amount to the backend field.
        const record = this.props?.record;
        if (record?.update) {
            const currentAmounts = Object.assign(
                {},
                record.data?.analytic_distribution_amounts || {}
            );
            currentAmounts[String(line.id)] = newAmount;
            await record.update({ analytic_distribution_amounts: currentAmounts });
        }

        ev.target.value = amountStr;
    },
});
