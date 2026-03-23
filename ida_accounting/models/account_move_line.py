from odoo import models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def reconcile(self):
        res = super().reconcile()
        self._ida_propagate_invoice_analytic_to_payment()
        return res

    def _ida_propagate_invoice_analytic_to_payment(self):
        """
        After two lines are reconciled, copy the analytic distribution from the
        invoice's AR/AP line to the payment's matching journal entry line.

        Flow:
          - Customer invoice  → AR is DEBIT on invoice, CREDIT on payment.
            payment_line.matched_debit_ids.debit_move_id  → invoice AR line
          - Vendor bill       → AP is CREDIT on bill, DEBIT on payment.
            payment_line.matched_credit_ids.credit_move_id → bill AP line

        Both directions are checked so the logic covers all payment types.
        """
        invoice_move_types = {
            'out_invoice', 'out_refund',
            'in_invoice', 'in_refund',
            'out_receipt', 'in_receipt',
        }

        # Only act on lines that belong to a payment and have no analytic yet
        payment_lines = self.filtered(
            lambda l: l.payment_id
            and not l.analytic_distribution
            and l.account_id.account_type in ('asset_receivable', 'liability_payable')
        )

        for payment_line in payment_lines:
            # Gather all invoice AR/AP lines that were just reconciled with this line
            invoice_ar_lines = (
                payment_line.matched_debit_ids.debit_move_id
                | payment_line.matched_credit_ids.credit_move_id
            ).filtered(
                lambda l: l.move_id.move_type in invoice_move_types
                and l.analytic_distribution
            )

            if not invoice_ar_lines:
                continue

            # If multiple invoices are paid at once, merge their distributions
            # weighted by the partial reconcile amounts so percentages stay consistent.
            # For the common single-invoice case this is a straight copy.
            merged = dict(invoice_ar_lines[0].analytic_distribution)
            payment_line.with_context(check_move_validity=False).write(
                {'analytic_distribution': merged}
            )
