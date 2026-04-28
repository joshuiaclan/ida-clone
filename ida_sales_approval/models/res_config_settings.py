from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_approval_required = fields.Boolean(
        string='Require Approval for Sales Quotations',
        config_parameter='ida_sales_approval.approval_required',
        help='When enabled, a quotation must pass all configured approval levels '
             'before it can be confirmed as a Sales Order.',
    )

    sale_approval_level_ids = fields.One2many(
        related='company_id.sale_approval_level_ids',
        string='Approval Levels',
        readonly=False,
    )
