from odoo import models, fields


class HrHolidayStatus(models.Model):
    _inherit = 'hr.leave.type'

    is_unpaid = fields.Boolean(
        string='Is Unpaid Time Off',
        help='When enabled, time off requests using this type will show '
             'an Unpaid Time Off Type field.',
    )
