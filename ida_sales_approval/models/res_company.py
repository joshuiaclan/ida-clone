from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_approval_level_ids = fields.One2many(
        'sale.approval.level',
        'company_id',
        string='Sale Approval Levels',
    )
