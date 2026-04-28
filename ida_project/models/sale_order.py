from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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

    def action_confirm(self):
        # Pre-generate BEFORE super() so _timesheet_create_project_prepare_values()
        # can read the number while projects are being created inside super().
        for order in self:
            if order.deal_type == 'new_project' and not order.base_project_number:
                order.base_project_number = order._generate_base_project_number()

        res = super().action_confirm()

        # After super(), all projects are created — assign the full number with
        # a two-digit sub-sequence to each project linked to this order.
        # Line-generated projects also get the product name appended.
        for order in self:
            if not (order.deal_type == 'new_project' and order.base_project_number):
                continue

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
                order.project_id.name = f"{order.base_project_number}-{idx:03d}"
                seen.add(order.project_id.id)
                idx += 1

            # Per-line projects — append product name
            for line in order.order_line:
                project = line.project_id
                if not project or project.id in seen:
                    continue
                product_name = line.product_id.name or ''
                suffix = f" {product_name}" if product_name else ''
                project.name = f"{order.base_project_number}-{idx:03d}{suffix}"
                seen.add(project.id)
                idx += 1

        return res
