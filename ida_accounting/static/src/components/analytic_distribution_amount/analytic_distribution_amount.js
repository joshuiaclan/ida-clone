/** @odoo-module **/

import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { patch } from "@web/core/utils/patch";
import { formatFloat } from "@web/views/fields/formatters";

/**
 * Patches AnalyticDistribution with a helper method used by the
 * analytic.AnalyticDistributionPopup template (rendered via t-call, so
 * `this` is still the AnalyticDistribution instance).
 *
 * Amount = parent line's base amount × (percentage / 100)
 *
 * The parent line amount is resolved from props.record.data in priority order:
 *   1. debit + credit  — account.move.line (Journal Items tab)
 *   2. price_subtotal  — account.move.line (Invoice Lines tab) / sale.order.line
 */
patch(AnalyticDistribution.prototype, {
    /**
     * @param {number|string} percentage  Distribution percentage (0–100).
     * @returns {string}  Formatted amount, e.g. "1,250.00"
     */
    idaGetAnalyticAmount(percentage) {
        const record = this.props.record;
        if (!record?.data) {
            return "";
        }

        const pct = parseFloat(percentage) || 0;

        const debit = record.data.debit ?? 0;
        const credit = record.data.credit ?? 0;
        const priceSubtotal = record.data.price_subtotal ?? 0;

        const baseAmount = (debit + credit) || Math.abs(priceSubtotal);
        const amount = baseAmount * (pct / 100);

        return formatFloat(amount, { digits: [false, 2] });
    },
});
