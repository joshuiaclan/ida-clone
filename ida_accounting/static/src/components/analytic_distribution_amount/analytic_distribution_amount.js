/** @odoo-module **/

import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";
import { formatFloat } from "@web/views/fields/formatters";

/**
 * Patches the AnalyticDistribution component to expose a method that computes
 * the monetary amount for each distribution line based on the parent record's
 * debit/credit (journal items) or price_subtotal (invoice/sale order lines).
 */
patch(AnalyticDistribution.prototype, {
    /**
     * Returns the computed amount for a distribution line.
     *
     * @param {number|string} percentage  The distribution percentage (0–100).
     * @returns {string}  Formatted amount string, e.g. "1,250.00"
     */
    idaGetAnalyticAmount(percentage) {
        const record = this.props.record;
        if (!record?.data) {
            return "";
        }

        const pct = parseFloat(percentage) || 0;

        // Journal item lines (account.move.line) carry debit / credit.
        // Invoice / SO lines carry price_subtotal.
        const debit = record.data.debit ?? 0;
        const credit = record.data.credit ?? 0;
        const priceSubtotal = record.data.price_subtotal ?? 0;

        // Use whichever amount source is available.
        const baseAmount = debit + credit || Math.abs(priceSubtotal);
        const amount = baseAmount * (pct / 100);

        return formatFloat(amount, { digits: [false, 2] });
    },
});
