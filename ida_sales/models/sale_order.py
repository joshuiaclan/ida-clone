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

    # Renamed from base_project_id (project.project) to free the name for
    # ida_project's base_project_id (ida.base.project).
    linked_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project Number',
        copy=False,
        tracking=True,
        help='Required when the order is linked to an existing or additional-services project.',
    )

    @api.onchange('deal_type')
    def _onchange_deal_type(self):
        if self.deal_type != 'existing_project':
            self.linked_project_id = False

    # ── PDF Printing Options ───────────────────────────────────────────────

    show_line_notes = fields.Boolean(
        string='Show Line Notes Instead of Price',
        default=False,
        help='When enabled, the PDF quotation hides the Unit Price and Amount '
             'columns and shows a Notes column per order line instead.',
    )

    # ── Agreement Acceptance fields (filled by client via portal) ─────────

    accepted_signature = fields.Binary(
        string='Acceptance Signature',
        copy=False,
        attachment=True,
        help='Client signature image captured on the portal.',
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
