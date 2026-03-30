from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    department_short_code = fields.Char(
        string='Department Short Code',
        size=10,
        help=(
            'Short code included as the department component of the '
            'Base Project Number when this product appears on a '
            'New Project sale order (e.g. "IT", "FIN", "OPS").'
        ),
    )
