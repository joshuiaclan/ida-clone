from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    deal_type = fields.Selection(
        selection=[
            ('new_project', 'New Project'),
            ('existing_project', 'Existing Project'),
            ('additional_services', 'Additional Services'),
        ],
        string='Deal Type',
        tracking=True,
    )

    base_project_number = fields.Char(
        string='Base Project Number',
        readonly=True,
        copy=False,
        tracking=True,
        help='Auto-generated when a New Project order is confirmed.',
    )

    base_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Base Project',
        copy=False,
        tracking=True,
        help='Required when the order is linked to an existing project.',
    )

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if order.deal_type == 'new_project' and not order.base_project_number:
                order.base_project_number = order._generate_base_project_number()
        return res

    def _generate_base_project_number(self):
        """Return the base project number for this order.

        Override in downstream modules (e.g. ida_project) to produce a
        fully-structured number.  The default implementation uses the simple
        ida.sales.project.number sequence defined in this module.
        """
        self.ensure_one()
        return self.env['ir.sequence'].next_by_code('ida.sales.project.number') or '/'

    @api.constrains('deal_type', 'base_project_id')
    def _check_existing_project_required(self):
        for order in self:
            if order.deal_type == 'existing_project' and not order.base_project_id:
                raise ValidationError(
                    _('A Base Project must be selected when Project Type is "Existing Project".')
                )

    @api.onchange('deal_type')
    def _onchange_deal_type(self):
        if self.deal_type != 'existing_project':
            self.base_project_id = False

    # ── Agreement Acceptance fields (filled by client via portal) ────────────

    accepted_signature_name = fields.Char(
        string='Signature',
        copy=False,
        help='Client signature name as entered on the portal.',
    )
    accepted_printed_name = fields.Char(
        string='Printed Name',
        copy=False,
    )
    accepted_email = fields.Char(
        string='Email Address',
        copy=False,
    )
    accepted_title = fields.Char(
        string='Title',
        copy=False,
    )
    accepted_date = fields.Date(
        string='Date',
        copy=False,
        help='Date the client accepted the agreement via the portal.',
    )
    accepted_legal_entity = fields.Char(
        string='Legal Entity',
        copy=False,
    )
    accepted_entity_address = fields.Char(
        string='Entity Address',
        copy=False,
    )
    accepted_invoice_email = fields.Char(
        string='Invoice Email',
        copy=False,
    )
