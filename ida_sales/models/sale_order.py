from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_type = fields.Selection(
        selection=[
            ('new_project', 'New Project'),
            ('existing_project', 'Existing Project'),
            ('additional_services', 'Additional Services'),
        ],
        string='Project Type',
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
            if order.project_type == 'new_project' and not order.base_project_number:
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

    @api.constrains('project_type', 'base_project_id')
    def _check_existing_project_required(self):
        for order in self:
            if order.project_type == 'existing_project' and not order.base_project_id:
                raise ValidationError(
                    _('A Base Project must be selected when Project Type is "Existing Project".')
                )

    @api.onchange('project_type')
    def _onchange_project_type(self):
        if self.project_type != 'existing_project':
            self.base_project_id = False
