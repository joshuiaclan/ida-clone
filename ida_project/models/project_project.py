from odoo import models, fields


class ProjectProject(models.Model):
    _inherit = 'project.project'

    base_project_id = fields.Many2one(
        'ida.base.project',
        string='Base Project',
        index=True,
        ondelete='set null',
    )
