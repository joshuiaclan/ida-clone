from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    base_project_id = fields.Many2one(
        'ida.base.project',
        string='Base Project',
        copy=False,
        tracking=True,
        ondelete='set null',
    )

    @api.onchange('linked_project_id')
    def _onchange_linked_project_id(self):
        """Auto-populate base_project_id from the selected project's base project."""
        if self.linked_project_id and self.linked_project_id.base_project_id:
            self.base_project_id = self.linked_project_id.base_project_id
        elif not self.linked_project_id:
            self.base_project_id = False

    def _generate_base_project_number(self):
        """Generate a structured project number: YY-NNNN.

        Format: {2-digit year}-{4-digit sequence}
        Example: 26-0001

        The sub-project index (-001, -002, …) is appended when the number is
        written to each project in action_confirm().
        """
        self.ensure_one()
        year = fields.Date.today().strftime('%y')
        seq = self.env['ir.sequence'].next_by_code('ida.project.main') or '0001'
        return f"{year}-{seq}"

    def _next_subproject_index(self, base_project, exclude_ids=None):
        """Return the next available 3-digit sub-sequence index for base_project.

        Scans all existing project.project records linked to base_project,
        extracts the numeric suffix (e.g. 1 from '26-0001-001'), and returns
        max + 1 so new subprojects continue the sequence instead of restarting.
        """
        domain = [('base_project_id', '=', base_project.id)]
        if exclude_ids:
            domain.append(('id', 'not in', list(exclude_ids)))

        existing = self.env['project.project'].search(domain)
        prefix = f"{base_project.number}-"
        max_idx = 0
        for proj in existing:
            if proj.name and proj.name.startswith(prefix):
                # The suffix is the 3-digit block immediately after the prefix
                suffix_part = proj.name[len(prefix):len(prefix) + 3]
                try:
                    max_idx = max(max_idx, int(suffix_part))
                except ValueError:
                    pass
        return max_idx + 1

    def action_confirm(self):
        # Pre-generate BEFORE super() so _timesheet_create_project_prepare_values()
        # can read base_project_id.number while projects are being created.
        for order in self:
            if order.deal_type == 'new_project' and not order.base_project_id:
                number = order._generate_base_project_number()
                base_project = self.env['ida.base.project'].create({
                    'number': number,
                })
                order.base_project_id = base_project

            # For existing_project, the onchange may not have been persisted to DB.
            # Resolve base_project_id server-side so the naming loop can run.
            elif order.deal_type == 'existing_project' and not order.base_project_id:
                if order.linked_project_id and order.linked_project_id.base_project_id:
                    order.base_project_id = order.linked_project_id.base_project_id

        res = super().action_confirm()

        # After super(), all projects are created — assign the full sub-sequence
        # number to each project and link them to the base project record.
        for order in self:
            if order.deal_type == 'additional_services':
                continue

            base_project = order.base_project_id
            if not base_project:
                continue

            seen = set()

            # Collect project IDs that belong to order lines
            line_project_ids = {
                line.project_id.id
                for line in order.order_line
                if line.project_id
            }

            # Gather all projects to be named in this run so we can exclude
            # them from the existing-index scan (they have no suffix yet).
            new_project_ids = set()
            if order.project_id and order.project_id.id not in line_project_ids:
                new_project_ids.add(order.project_id.id)
            for line in order.order_line:
                if line.project_id:
                    new_project_ids.add(line.project_id.id)

            # Start from the next available index after existing subprojects
            idx = self._next_subproject_index(base_project, exclude_ids=new_project_ids)

            # Main order project — only if it is not also a line project
            if order.project_id and order.project_id.id not in line_project_ids:
                order.project_id.write({
                    'name': f"{base_project.number}-{idx:03d}",
                    'base_project_id': base_project.id,
                })
                seen.add(order.project_id.id)
                idx += 1

            # Per-line projects — name and link to base project
            for line in order.order_line:
                project = line.project_id
                if not project or project.id in seen:
                    continue
                project.write({
                    'name': f"{base_project.number}-{idx:03d}",
                    'base_project_id': base_project.id,
                })
                seen.add(project.id)
                idx += 1

        return res
