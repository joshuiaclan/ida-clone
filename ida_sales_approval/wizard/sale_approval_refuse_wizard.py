from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleApprovalRefuseWizard(models.TransientModel):
    _name = 'sale.approval.refuse.wizard'
    _description = 'Sales Approval Refusal Wizard'

    order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        required=True,
        readonly=True,
    )
    note = fields.Text(
        string='Reason for Refusal',
        required=True,
        help='This reason will be recorded on the approval record and posted in the chatter.',
    )

    def action_confirm_refusal(self):
        """Apply the refusal to the order."""
        self.ensure_one()
        order = self.order_id
        uid = self.env.uid

        pending = order.approval_ids.filtered(
            lambda a: a.approver_id.id == uid
            and a.state == 'pending'
            and a.level_id == order.current_approval_level_id
        )
        if not pending:
            raise UserError(_(
                'You are not an approver for the current level, '
                'or you have already responded to this request.'
            ))

        now = fields.Datetime.now()

        # Mark this approver's record as refused
        pending.write({'state': 'refused', 'date': now, 'note': self.note})

        # Cancel any remaining pending approvals on the order
        order.approval_ids.filtered(
            lambda a: a.state == 'pending'
        ).write({'state': 'refused', 'date': now})

        order.write({
            'approval_state': 'refused',
            'current_approval_level_id': False,
        })

        order.message_post(
            body=_(
                'This quotation has been <b>refused</b> by %s.<br/>'
                '<b>Reason:</b> %s'
            ) % (self.env.user.name, self.note),
        )
        return {'type': 'ir.actions.act_window_close'}
