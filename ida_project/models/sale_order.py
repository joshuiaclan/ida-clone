from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ── New fields ────────────────────────────────────────────────────────────

    project_location_id = fields.Many2one(
        comodel_name='ida.project.location',
        string='Project Location',
        tracking=True,
        help='Physical or logical location of the project. '
             'Used as a component of the Base Project Number.',
    )

    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        tracking=True,
        help='Responsible department. '
             'Its code (or first 3 letters of the name) forms part of the '
             'Base Project Number.',
    )

    # ── Confirmation hook ─────────────────────────────────────────────────────

    def action_confirm(self):
        """After confirmation, propagate the generated number to the project."""
        res = super().action_confirm()
        for order in self:
            if order.project_type == 'new_project' and order.base_project_number:
                # sale_project links the SO to a project via project_id.
                # Write the structured number (and location) to that project.
                if order.project_id:
                    order.project_id.write({
                        'base_project_number': order.base_project_number,
                        'project_location_id': order.project_location_id.id,
                    })
        return res

    # ── Project number generation (overrides ida_sales hook) ─────────────────

    def _generate_base_project_number(self):
        """
        Build the structured project number:

            {YEAR} - {DEPT_CODE} - {SEQ} - {LOC_SEQ}

        e.g.  2026-IT-001-01

        Components
        ──────────
        YEAR      – 4-digit year of today's date (confirmation date).
        DEPT_CODE – department.code, or first 3 chars of department.name
                    (upper-cased) when no explicit code is set.
        SEQ       – 3-digit number from the yearly-reset ir.sequence
                    "ida.project.number".  Resets to 001 on 1 Jan each year.
        LOC_SEQ   – "final suffix": 2-digit sequential count of New-Project
                    sale orders at the same Project Location confirmed in
                    the same calendar year.  Computed in the backend at the
                    moment the sequence is generated.

        Raises UserError when Project Location or Department is not set,
        because both are required to build the number.
        """
        self.ensure_one()

        if not self.project_location_id:
            raise UserError(_(
                'Project Location is required for "New Project" orders '
                'before the order can be confirmed.\n'
                'Please set the Project Location on the order form.'
            ))
        if not self.department_id:
            raise UserError(_(
                'Department is required for "New Project" orders '
                'before the order can be confirmed.\n'
                'Please set the Department on the order form.'
            ))

        today = fields.Date.context_today(self)
        year = today.year

        # ── 1. Yearly sequential number (Odoo sequence, auto-resets each year)
        seq = self.env['ir.sequence'].next_by_code('ida.project.number') or '001'

        # ── 2. Department code
        dept = self.department_id
        dept_code = (dept.code or dept.name[:3]).strip().upper()

        # ── 3. Location sequence — "final suffix added in the backend"
        #    Count confirmed New-Project orders at the same location
        #    within the current calendar year (excluding this order).
        year_start = today.replace(month=1, day=1)
        year_end = today.replace(year=year + 1, month=1, day=1)

        prior_count = self.env['sale.order'].search_count([
            ('id', '!=', self.id),
            ('project_type', '=', 'new_project'),
            ('project_location_id', '=', self.project_location_id.id),
            ('state', 'in', ('sale', 'done')),
            ('date_order', '>=', fields.Date.to_string(year_start)),
            ('date_order', '<', fields.Date.to_string(year_end)),
        ])
        loc_seq = str(prior_count + 1).zfill(2)

        # ── Combine: YEAR-DEPT_CODE-SEQ-LOC_SEQ
        return f"{year}-{dept_code}-{seq}-{loc_seq}"

    # ── Onchange helpers ──────────────────────────────────────────────────────

    @api.onchange('project_type')
    def _onchange_project_type_ida_project(self):
        """Clear location and department when the order is not a new project."""
        if self.project_type != 'new_project':
            self.project_location_id = False
            self.department_id = False
