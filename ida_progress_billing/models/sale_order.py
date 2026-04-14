from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False, date=None):
        """After creating the invoice, reset amount_to_bill and percent_to_bill
        on the invoiced lines so the same amount is not billed again next period."""
        lines_to_reset = self.order_line.filtered(
            lambda l: l.amount_to_bill > 0 and l.qty_to_invoice > 0
        )
        invoices = super()._create_invoices(grouped=grouped, final=final, date=date)
        lines_to_reset.write({'amount_to_bill': 0.0, 'percent_to_bill': 0.0})
        return invoices
