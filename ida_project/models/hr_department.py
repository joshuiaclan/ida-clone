from odoo import models, fields


class HrDepartment(models.Model):
    """Adds a short Department Code used as a component of the project number."""
    _inherit = 'hr.department'

    code = fields.Char(
        string='Department Code',
        size=10,
        help=(
            'Short code included in the Base Project Number '
            '(e.g. "IT", "FIN", "OPS"). '
            'If left blank, the first three letters of the department name '
            'are used automatically.'
        ),
    )
