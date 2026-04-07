from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    percent_complete = fields.Float(
        string='% Complete',
        digits=(5, 2),
        default=0.0,
        help='Percentage of work completed for this line item.',
    )

    amount_to_bill = fields.Monetary(
        string='Amount to Bill',
        compute='_compute_amount_to_bill',
        store=True,
        currency_field='currency_id',
        help='Amount to be billed based on the percent complete '
             '(% Complete × Contract Amount).',
    )

    @api.depends('percent_complete', 'price_unit')
    def _compute_amount_to_bill(self):
        for line in self:
            print(line.percent_complete)
            line.amount_to_bill = line.price_unit * (line.percent_complete)

    def _prepare_invoice_line(self, **optional_values):
        """Carry percent_complete and contract_amount to the invoice line.

        When percent_complete is set, the invoiced price_unit is adjusted so
        the invoice line total equals amount_to_bill (percent_complete % of
        the contracted line total).
        """
        res = super()._prepare_invoice_line(**optional_values)

        res['percent_complete'] = self.percent_complete
        res['contract_amount'] = self.price_subtotal

        if self.percent_complete and self.product_uom_qty:
            res['price_unit'] = self.amount_to_bill / self.product_uom_qty

        return res
