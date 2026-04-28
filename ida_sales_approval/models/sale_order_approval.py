from odoo import models, fields


class SaleOrderApproval(models.Model):
    _name = 'sale.order.approval'
    _description = 'Sales Order Approval Record'
    _order = 'level_sequence, id'

    order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    level_id = fields.Many2one(
        'sale.approval.level',
        string='Approval Level',
        required=True,
        ondelete='restrict',
    )
    level_sequence = fields.Integer(
        related='level_id.sequence',
        store=True,
        string='Level Order',
    )
    approver_id = fields.Many2one(
        'res.users',
        string='Approver',
        required=True,
        ondelete='restrict',
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
        ],
        string='Status',
        default='pending',
        required=True,
    )
    date = fields.Datetime(string='Date')
    note = fields.Text(string='Note / Reason')
