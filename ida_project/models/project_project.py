from odoo import models, fields


class ProjectProject(models.Model):
    """Stores the Project Location propagated from the originating sale order.

    The Base Project Number itself is written to the project's standard
    `name` field when the sale order is confirmed, so no separate field
    is needed here.
    """
    _inherit = 'project.project'

    project_location_id = fields.Many2one(
        comodel_name='ida.project.location',
        string='Project Location',
        copy=False,
        tracking=True,
    )
