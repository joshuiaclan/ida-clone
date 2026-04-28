from odoo import models, fields


class IdaBaseProject(models.Model):
    _name = 'ida.base.project'
    _description = 'Base Project'
    _order = 'number'

    number = fields.Char(
        string='Number',
        required=True,
        readonly=True,
        copy=False,
        index=True,
    )
    location = fields.Char(
        string='Location',
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        readonly=True,
        ondelete='set null',
    )
