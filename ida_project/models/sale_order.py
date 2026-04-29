from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    base_project_id = fields.Many2one(
        'ida.base.project',
        string='Base Project',
        copy=False,
        index=True,
        ondelete='set null',
    )

    def _generate_base_project_number(self):
        """Generate a structured project number: YY-NNNN.

        Format: {2-digit year}-{4-digit sequence}
        Example: 26-0001

        The sub-project index (-001, -002, …) is appended when the number is
        written to each project in action_confirm().
        """
        self.ensure_one()
        year = fields.Date.today().strftime('%y')   # 2-digit year, e.g. "26"
        seq = self.env['ir.sequence'].next_by_code('ida.project.main') or '0001'
        return f"{year}-{seq}"

    @api.onchange('project_id')
    def _onchange_project_id_base_project(self):
        if self.project_id and self.project_id.base_project_id:
            self.base_project_id = self.project_id.base_project_id
        else:
            self.base_project_id = False

    def action_confirm(self):
        # Pre-generate BEFORE super() so _timesheet_create_project_prepare_values()
        # can read the number while projects are being created inside super().
        base_projects = {}  # order.id -> ida.base.project record
        for order in self:
            if order.deal_type == 'new_project' and not order.base_project_number:
                number = order._generate_base_project_number()
                order.base_project_number = number
                base_project = self.env['ida.base.project'].create({
                    'number': number,
                    'sale_order_id': order.id,
                })
                order.base_project_id = base_project
                base_projects[order.id] = base_project

        res = super().action_confirm()

        # After super(), all projects are created — assign the full number with
        # a three-digit sub-sequence to each project linked to this order.
        # Also link each subproject to its ida.base.project record.
        for order in self:
            if not (order.deal_type == 'new_project' and order.base_project_number):
                continue

            base_project = base_projects.get(order.id) or self.env['ida.base.project'].search(
                [('sale_order_id', '=', order.id)], limit=1
            )

            idx = 1
            seen = set()

            # Collect project IDs that belong to order lines
            line_project_ids = {
                line.project_id.id
                for line in order.order_line
                if line.project_id
            }

            # Main order project — only if it is not also a line project
            if order.project_id and order.project_id.id not in line_project_ids:
                order.project_id.write({
                    'name': f"{order.base_project_number}-{idx:03d}",
                    'base_project_id': base_project.id if base_project else False,
                })
                seen.add(order.project_id.id)
                idx += 1

            # Per-line projects — name and link to base project
            for line in order.order_line:
                project = line.project_id
                if not project or project.id in seen:
                    continue
                project.write({
                    'name': f"{order.base_project_number}-{idx:03d}",
                    'base_project_id': base_project.id if base_project else False,
                })
                seen.add(project.id)
                idx += 1

        return res
