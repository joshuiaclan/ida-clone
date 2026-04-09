from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # ── Existing fields ───────────────────────────────────────────────────────

    percent_complete = fields.Float(
        string='% Complete',
        digits=(5, 2),
        default=0.0,
        help='Percentage billed this period (carried from the sale order line).',
    )

    contract_amount = fields.Monetary(
        string='Contract Amount',
        currency_field='currency_id',
        help='Original contracted amount for this line (from the sale order).',
    )

    # ── New computed fields ───────────────────────────────────────────────────

    prior_billed = fields.Monetary(
        string='Prior Billed',
        compute='_compute_prior_billed_aml',
        currency_field='currency_id',
        help='Total amount billed on other posted invoices for the same sale order line.',
    )

    total_billed = fields.Monetary(
        string='Total Billed',
        compute='_compute_billing_totals_aml',
        currency_field='currency_id',
        help='Prior Billed + this invoice line amount.',
    )

    total_percent_billed = fields.Float(
        string='Total Percent Billed',
        digits=(5, 2),
        compute='_compute_billing_totals_aml',
        help='Total Billed as a percentage of the Contract Amount.',
    )

    total_billed_amount = fields.Monetary(
        string='Total Billed Amount',
        compute='_compute_billing_totals_aml',
        currency_field='currency_id',
        help='Contract Amount × Total Percent Billed / 100.',
    )

    # ── Compute: Prior Billed ─────────────────────────────────────────────────

    @api.depends(
        'sale_line_ids.invoice_lines.move_id.state',
        'sale_line_ids.invoice_lines.move_id.move_type',
        'sale_line_ids.invoice_lines.price_subtotal',
    )
    def _compute_prior_billed_aml(self):
        for line in self:
            billed = 0.0
            for sol in line.sale_line_ids:
                for inv_line in sol.invoice_lines:
                    if inv_line.id == line.id:
                        continue  # exclude self
                    if inv_line.move_id.state != 'posted':
                        continue
                    if inv_line.move_id.move_type == 'out_invoice':
                        billed += inv_line.price_subtotal
                    elif inv_line.move_id.move_type == 'out_refund':
                        billed -= inv_line.price_subtotal
            line.prior_billed = billed

    # ── Compute: Billing Totals ───────────────────────────────────────────────

    @api.depends('prior_billed', 'price_subtotal', 'contract_amount')
    def _compute_billing_totals_aml(self):
        for line in self:
            total = line.prior_billed + line.price_subtotal
            line.total_billed = total
            if line.contract_amount:
                pct = total / line.contract_amount
            else:
                pct = 0.0
            line.total_percent_billed = pct
            line.total_billed_amount = line.contract_amount * pct
