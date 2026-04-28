from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleApprovalLevel(models.Model):
    _name = 'sale.approval.level'
    _description = 'Sales Quotation Approval Level'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Order', default=10)
    name = fields.Char(string='Level Name', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    approver_ids = fields.Many2many(
        'res.users',
        'sale_approval_level_user_rel',
        'level_id',
        'user_id',
        string='Approvers',
        domain=[('share', '=', False)],
    )
    required_approvals = fields.Integer(
        string='Required Approvals',
        default=1,
        help='Minimum number of approvers from this level that must approve '
             'before the workflow advances to the next level. '
             'Set to 1 to allow any single approver to advance the flow.',
    )

    @api.constrains('required_approvals', 'approver_ids')
    def _check_required_approvals(self):
        for level in self:
            if level.required_approvals < 1:
                raise ValidationError(
                    'Required Approvals must be at least 1 on level "%s".' % level.name
                )
            if level.approver_ids and level.required_approvals > len(level.approver_ids):
                raise ValidationError(
                    'Required Approvals (%d) cannot exceed the number of assigned '
                    'approvers (%d) on level "%s".' % (
                        level.required_approvals,
                        len(level.approver_ids),
                        level.name,
                    )
                )
