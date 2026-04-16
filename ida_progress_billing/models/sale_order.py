from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Progress-billing invoice creation.

        1. Lines with percent_to_bill or amount_to_bill > 0 are invoiced normally
           (price = amount_to_bill) via the overridden qty_to_invoice / _prepare_invoice_line.
        2. All remaining SO lines (price = 0) are appended to the same invoice so
           the customer can see the full scope of work.
        3. After the invoice is created, percent_to_bill and amount_to_bill are
           reset to 0 so the same values are not double-billed next period.
        """
        # Track which lines triggered invoicing (will be reset afterwards)
        lines_to_reset = self.order_line.filtered(
            lambda l: l.amount_to_bill > 0 or l.percent_to_bill > 0
        )

        invoices = super()._create_invoices(grouped=grouped, final=final, date=date)

        # ── Append zero-price lines for customer viewing ──────────────────────
        for invoice in invoices:
            # SO lines that already have an invoice line on this invoice
            invoiced_sol = invoice.invoice_line_ids.mapped('sale_line_ids')

            # Orders that contributed at least one line to this invoice
            contributing_orders = invoiced_sol.mapped('order_id') & self

            for order in contributing_orders:
                # Remaining lines: confirmed, have a product, not yet on invoice
                zero_lines = order.order_line.filtered(
                    lambda l: l not in invoiced_sol
                    and l.product_id
                    and not l.display_type
                    and l.state in ('sale', 'done')
                )
                for sol in zero_lines:
                    vals = sol._prepare_invoice_line()
                    vals['move_id'] = invoice.id
                    # Force price to 0 — these lines are for viewing only
                    vals['price_unit'] = 0.0
                    self.env['account.move.line'].create(vals)

        # ── Reset billing fields so next period starts fresh ──────────────────
        lines_to_reset.write({'amount_to_bill': 0.0, 'percent_to_bill': 0.0})

        return invoices
