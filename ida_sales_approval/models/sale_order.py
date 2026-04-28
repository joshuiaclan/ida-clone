from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ── Approval state ────────────────────────────────────────────────────────

    approval_state = fields.Selection(
        selection=[
            ('for_approval', 'For Approval'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
        ],
        string='Approval Status',
        copy=False,
        tracking=True,
        index=True,
    )

    current_approval_level_id = fields.Many2one(
        'sale.approval.level',
        string='Current Approval Level',
        copy=False,
    )

    approval_ids = fields.One2many(
        'sale.order.approval',
        'order_id',
        string='Approvals',
    )

    # ── Computed helpers used in view conditions ──────────────────────────────

    approval_required = fields.Boolean(
        compute='_compute_approval_required',
        string='Approval Required',
    )

    is_current_approver = fields.Boolean(
        compute='_compute_is_current_approver',
        string='Is Current Approver',
    )

    @api.depends_context('uid')
    def _compute_approval_required(self):
        required = bool(
            self.env['ir.config_parameter'].sudo().get_param(
                'ida_sales_approval.approval_required'
            )
        )
        for order in self:
            order.approval_required = required

    @api.depends('approval_ids.state', 'approval_ids.approver_id',
                 'current_approval_level_id')
    def _compute_is_current_approver(self):
        uid = self.env.uid
        for order in self:
            order.is_current_approver = any(
                a.approver_id.id == uid
                and a.state == 'pending'
                and a.level_id == order.current_approval_level_id
                for a in order.approval_ids
            )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_approval_levels(self):
        return self.env['sale.approval.level'].search(
            [('company_id', '=', self.company_id.id)],
            order='sequence, id',
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_submit_approval(self):
        """Submit the quotation for approval — creates approval records for level 1."""
        self.ensure_one()
        if self.state not in ('draft', 'sent'):
            raise UserError(_('Only draft or sent quotations can be submitted for approval.'))

        levels = self._get_approval_levels()
        if not levels:
            raise UserError(_(
                'No approval levels are configured for this company. '
                'Please go to Sales > Configuration > Settings and set up '
                'approval levels before submitting.'
            ))

        first_level = levels[0]
        if not first_level.approver_ids:
            raise UserError(_(
                'Approval level "%s" has no approvers assigned. '
                'Please assign approvers in Sales Configuration.'
            ) % first_level.name)

        # Clear any previous approval records
        self.approval_ids.unlink()

        # Create pending approval records for every approver in level 1
        for user in first_level.approver_ids:
            self.env['sale.order.approval'].create({
                'order_id': self.id,
                'level_id': first_level.id,
                'approver_id': user.id,
                'state': 'pending',
            })

        self.write({
            'approval_state': 'for_approval',
            'current_approval_level_id': first_level.id,
        })

        approver_names = ', '.join(first_level.approver_ids.mapped('name'))
        self.message_post(
            body=_(
                'Quotation submitted for approval.<br/>'
                '<b>Level:</b> %s<br/>'
                '<b>Awaiting approval from:</b> %s'
            ) % (first_level.name, approver_names),
            partner_ids=first_level.approver_ids.mapped('partner_id').ids,
        )
        return True

    def action_approve(self):
        """Record the current user's approval and advance the workflow."""
        self.ensure_one()
        uid = self.env.uid

        pending = self.approval_ids.filtered(
            lambda a: a.approver_id.id == uid
            and a.state == 'pending'
            and a.level_id == self.current_approval_level_id
        )
        if not pending:
            raise UserError(_(
                'You are not an approver for the current level, '
                'or you have already responded to this request.'
            ))

        pending.write({'state': 'approved', 'date': fields.Datetime.now()})

        level = self.current_approval_level_id
        approved_count = self.approval_ids.filtered(
            lambda a: a.level_id == level and a.state == 'approved'
        )

        # Check whether this level's required approvals threshold has been met
        if len(approved_count) >= level.required_approvals:
            all_levels = self._get_approval_levels()
            ids_list = all_levels.ids
            try:
                current_idx = ids_list.index(level.id)
            except ValueError:
                current_idx = -1

            next_levels = all_levels.filtered(
                lambda l: ids_list.index(l.id) > current_idx
            ) if current_idx >= 0 else self.env['sale.approval.level']

            if next_levels:
                # Advance to the next level
                next_level = next_levels[0]
                if not next_level.approver_ids:
                    raise UserError(_(
                        'Approval level "%s" has no approvers assigned.'
                    ) % next_level.name)

                for user in next_level.approver_ids:
                    self.env['sale.order.approval'].create({
                        'order_id': self.id,
                        'level_id': next_level.id,
                        'approver_id': user.id,
                        'state': 'pending',
                    })
                self.current_approval_level_id = next_level

                approver_names = ', '.join(next_level.approver_ids.mapped('name'))
                self.message_post(
                    body=_(
                        'Level <b>%s</b> approved. Advancing to next level.<br/>'
                        '<b>Level:</b> %s<br/>'
                        '<b>Awaiting approval from:</b> %s'
                    ) % (level.name, next_level.name, approver_names),
                    partner_ids=next_level.approver_ids.mapped('partner_id').ids,
                )
            else:
                # All levels completed — fully approved
                self.write({
                    'approval_state': 'approved',
                    'current_approval_level_id': False,
                })
                self.message_post(
                    body=_(
                        'All approval levels completed. '
                        'This quotation is <b>approved</b> and may now be confirmed.'
                    ),
                )
        else:
            # Level threshold not yet met — notify remaining count
            remaining = level.required_approvals - len(approved_count)
            self.message_post(
                body=_(
                    '<b>%s</b> approved this quotation. '
                    '%d more approval(s) required for level "%s".'
                ) % (self.env.user.name, remaining, level.name),
            )
        return True

    def action_refuse(self):
        """Open the refusal wizard to capture a reason."""
        self.ensure_one()
        uid = self.env.uid

        pending = self.approval_ids.filtered(
            lambda a: a.approver_id.id == uid
            and a.state == 'pending'
            and a.level_id == self.current_approval_level_id
        )
        if not pending:
            raise UserError(_(
                'You are not an approver for the current level, '
                'or you have already responded to this request.'
            ))

        return {
            'name': _('Refuse Quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.approval.refuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }

    def action_reset_approval(self):
        """Reset a refused or submitted quotation back to draft for resubmission."""
        self.ensure_one()
        self.write({
            'approval_state': False,
            'current_approval_level_id': False,
        })
        self.approval_ids.unlink()
        self.message_post(body=_('Approval reset. Quotation returned to draft state.'))
        return True

    # ── Confirm override ──────────────────────────────────────────────────────

    def action_confirm(self):
        """Block confirmation when approval is required but not yet granted."""
        approval_required = bool(
            self.env['ir.config_parameter'].sudo().get_param(
                'ida_sales_approval.approval_required'
            )
        )
        if approval_required:
            for order in self:
                if order.state in ('draft', 'sent') and order.approval_state != 'approved':
                    raise UserError(_(
                        'Quotation "%s" requires approval before it can be confirmed. '
                        'Please submit it for approval first.'
                    ) % order.name)
        return super().action_confirm()
