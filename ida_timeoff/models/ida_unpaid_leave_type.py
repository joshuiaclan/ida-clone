from odoo import models, fields


class IdaUnpaidLeaveType(models.Model):
    _name = 'ida.unpaid.leave.type'
    _description = 'Unpaid Time Off Type'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(default=True)
