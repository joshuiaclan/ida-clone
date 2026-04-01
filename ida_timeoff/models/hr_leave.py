from odoo import models, fields


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    leave_is_unpaid = fields.Boolean(
        related='holiday_status_id.is_unpaid',
        string='Leave Is Unpaid',
        store=False,
    )

    unpaid_leave_type_id = fields.Many2one(
        comodel_name='ida.unpaid.leave.type',
        string='Unpaid Time Off Type',
        tracking=True,
    )
