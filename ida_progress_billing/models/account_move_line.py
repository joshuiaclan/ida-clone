from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    percent_complete = fields.Float(
        string='% Complete',
        digits=(5, 2),
        default=0.0,
        help='Percentage of work completed carried from the sale order line.',
    )

    contract_amount = fields.Monetary(
        string='Contract Amount',
        currency_field='currency_id',
        help='Original contracted amount for this line (from the sale order).',
    )
