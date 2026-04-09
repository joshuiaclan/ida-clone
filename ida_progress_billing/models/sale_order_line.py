from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ── Existing fields ───────────────────────────────────────────────────────

    percent_complete = fields.Float(
        string='% Complete',
        digits=(5, 2),
        default=0.0,
        help='Total percentage of work completed for this line item.',
    )

    # amount_to_bill is now a regular editable field (not computed) so it can
    # be driven bidirectionally with percent_to_bill via onchange.
    amount_to_bill = fields.Monetary(
        string='Amount to Bill',
        store=True,
        currency_field='currency_id',
        help='Amount to be billed this period (Percent to Bill × Contract Amount).',
    )

    # ── New fields ────────────────────────────────────────────────────────────

    percent_to_bill = fields.Float(
        string='Percent to Bill',
        digits=(5, 2),
        default=0.0,
        help='Percentage of the contract amount to bill in the current period. '
             'Updating this recalculates Amount to Bill and vice-versa.',
    )

    prior_billed = fields.Monetary(
        string='Prior Billed',
        compute='_compute_prior_billed',
        currency_field='currency_id',
        help='Total amount already billed on previously posted invoices for this line.',
    )

    total_billed = fields.Monetary(
        string='Total Billed',
        compute='_compute_billing_totals',
        currency_field='currency_id',
        help='Prior Billed + Amount to Bill.',
    )

    total_percent_billed = fields.Float(
        string='Total Percent Billed',
        digits=(5, 2),
        compute='_compute_billing_totals',
        help='Total Billed as a percentage of the Contract Amount (Subtotal).',
    )

    total_billed_amount = fields.Monetary(
        string='Total Billed Amount',
        compute='_compute_billing_totals',
        currency_field='currency_id',
        help='Contract Amount × Total Percent Billed / 100.',
    )

    # ── Compute: Prior Billed ─────────────────────────────────────────────────

    @api.depends(
        'invoice_lines.move_id.state',
        'invoice_lines.move_id.move_type',
        'invoice_lines.price_subtotal',
    )
    def _compute_prior_billed(self):
        for line in self:
            billed = 0.0
            for inv_line in line.invoice_lines:
                if inv_line.move_id.state != 'posted':
                    continue
                if inv_line.move_id.move_type == 'out_invoice':
                    billed += inv_line.price_subtotal
                elif inv_line.move_id.move_type == 'out_refund':
                    billed -= inv_line.price_subtotal
            line.prior_billed = billed

    # ── Compute: Billing Totals ───────────────────────────────────────────────

    @api.depends('prior_billed', 'amount_to_bill', 'price_subtotal')
    def _compute_billing_totals(self):
        for line in self:
            total = line.prior_billed + line.amount_to_bill
            line.total_billed = total
            if line.price_subtotal:
                pct = total / line.price_subtotal * 100.0
            else:
                pct = 0.0
            line.total_percent_billed = pct
            line.total_billed_amount = line.price_subtotal * pct / 100.0

    # ── Onchange: bidirectional percent_to_bill ↔ amount_to_bill ─────────────

    @api.onchange('percent_to_bill')
    def _onchange_percent_to_bill(self):
        self.amount_to_bill = self.price_subtotal * (self.percent_to_bill / 100.0)

    @api.onchange('amount_to_bill')
    def _onchange_amount_to_bill(self):
        if self.price_subtotal:
            self.percent_to_bill = self.amount_to_bill / self.price_subtotal * 100.0

    # ── Invoice line preparation ──────────────────────────────────────────────

    def _prepare_invoice_line(self, **optional_values):
        """Carry progress billing data to the invoice line.

        price_unit is adjusted so the invoice line total equals amount_to_bill.
        percent_to_bill is stored on the invoice line as percent_complete.
        """
        res = super()._prepare_invoice_line(**optional_values)

        res['percent_complete'] = self.percent_to_bill
        res['contract_amount'] = self.price_subtotal

        if self.amount_to_bill and self.product_uom_qty:
            res['price_unit'] = self.amount_to_bill / self.product_uom_qty

        return res
