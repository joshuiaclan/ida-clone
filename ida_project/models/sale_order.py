from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _generate_base_project_number(self):
        """Generate a structured project number: YYYY-NNN.

        The sub-project index (-01, -02, …) is appended when the number is
        written to each project in action_confirm().
        """
        self.ensure_one()
        year = fields.Date.today().year
        seq = self.env['ir.sequence'].next_by_code('ida.project.main') or '001'
        return f"{year}-{seq}"

    def action_confirm(self):
        # Pre-generate BEFORE super() so _timesheet_create_project_prepare_values()
        # can read the number while projects are being created inside super().
        for order in self:
            if order.deal_type == 'new_project' and not order.base_project_number:
                order.base_project_number = order._generate_base_project_number()

        res = super().action_confirm()

        # After super(), all projects are created — assign the full number with
        # a two-digit sub-sequence to each project linked to this order.
        for order in self:
            if not (order.deal_type == 'new_project' and order.base_project_number):
                continue

            projects = (
                order.project_id | order.order_line.mapped('project_id')
            ).filtered('id')

            for idx, project in enumerate(projects, start=1):
                project.name = f"{order.base_project_number}-{idx:02d}"

        return res
