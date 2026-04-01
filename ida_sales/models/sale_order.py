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
                order.base_project_number = (
                    self.env['ir.sequence'].next_by_code('ida.sales.project.number') or '/'
                )
        return res

    @api.onchange('deal_type')
    def _onchange_deal_type(self):
        if self.deal_type != 'existing_project':
            self.base_project_id = False
