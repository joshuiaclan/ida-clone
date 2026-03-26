from odoo import models, fields


class IdaProjectLocation(models.Model):
    _name = 'ida.project.location'
    _description = 'Project Location'
    _order = 'name'

    name = fields.Char(
        string='Location Name',
        required=True,
    )
    code = fields.Char(
        string='Location Code',
        required=True,
        help='Short identifier used internally (e.g. "MNL", "CDO").',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Location Code must be unique.'),
    ]
