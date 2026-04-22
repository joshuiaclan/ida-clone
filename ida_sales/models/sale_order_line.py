from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_note = fields.Text(
        string='Notes',
        help='Optional note shown in the PDF quotation when '
             '"Show Line Notes Instead of Price" is enabled on the order.',
    )
