from odoo import models, fields


class ProjectProject(models.Model):
    """Stores the structured project number generated from the linked sale order."""
    _inherit = 'project.project'

    base_project_number = fields.Char(
        string='Base Project Number',
        readonly=True,
        copy=False,
        tracking=True,
        help='Structured project number assigned when the originating Sales Order is confirmed.',
    )

    project_location_id = fields.Many2one(
        comodel_name='ida.project.location',
        string='Project Location',
        copy=False,
        tracking=True,
    )
