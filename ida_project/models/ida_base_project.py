from odoo import models, fields, api


class IdaBaseProject(models.Model):
    _name = 'ida.base.project'
    _description = 'Base Project'
    _rec_name = 'name'
    _order = 'number'

    number = fields.Char(
        string='Number',
        required=True,
        readonly=True,
        copy=False,
        index=True,
    )
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        readonly=True,
    )
    location = fields.Char(
        string='Location',
    )
    project_ids = fields.One2many(
        'project.project',
        'base_project_id',
        string='Sub Projects',
        readonly=True,
    )

    @api.depends('number')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.number
