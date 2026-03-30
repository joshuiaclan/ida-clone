from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_location_id = fields.Many2one(
        comodel_name='ida.project.location',
        string='Project Location',
        tracking=True,
        help=(
            'Physical or logical location of the project. '
            'Used as a component of the Base Project Number and '
            'copied to the linked project on confirmation.'
        ),
    )

    # ── Confirmation ──────────────────────────────────────────────────────────

    def action_confirm(self):
        """After the number is generated (by ida_sales calling
        _generate_base_project_number), write it — plus the location — to the
        linked project's *name* field so no extra field is required on
        project.project.
        """
        res = super().action_confirm()
        for order in self:
            if order.project_type == 'new_project' and order.base_project_number:
                if order.project_id:
                    order.project_id.write({
                        'name': order.base_project_number,
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
        YEAR      – 4-digit confirmation year.
        DEPT_CODE – `department_short_code` of the first sale order line
                    whose product has that field populated (upper-cased).
        SEQ       – 3-digit number from the yearly-reset ir.sequence
                    "ida.project.number" (resets to 001 on 1 Jan each year).
        LOC_SEQ   – 2-digit count of other confirmed New-Project orders at
                    the same Project Location in the same calendar year + 1.
                    This is the "final suffix added in the backend at the
                    moment the sequence is generated."

        Raises UserError if Project Location is not set or no sale order
        line carries a product with a Department Short Code.
        """
        self.ensure_one()

        if not self.project_location_id:
            raise UserError(_(
                'Project Location is required for "New Project" orders.\n'
                'Please set it on the order before confirming.'
            ))

        # Resolve department code from the first product line that has one
        dept_code = ''
        for line in self.order_line:
            code = (line.product_id.department_short_code or '').strip().upper()
            if code:
                dept_code = code
                break

        if not dept_code:
            raise UserError(_(
                'At least one sale order line must have a product with a '
                '"Department Short Code" set before this order can be confirmed.'
            ))

        today = fields.Date.context_today(self)
        year = today.year

        # ── 1. Yearly sequential number (auto-resets via ir.sequence date_range)
        seq = self.env['ir.sequence'].next_by_code('ida.project.number') or '001'

        # ── 2. Location sequence — the "final suffix added in the backend"
        #    Count other confirmed New-Project orders at the same location
        #    within the same calendar year.
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

    # ── Onchange ──────────────────────────────────────────────────────────────

    @api.onchange('project_type')
    def _onchange_project_type_ida_project(self):
        """Clear location when the order is no longer a new project."""
        if self.project_type != 'new_project':
            self.project_location_id = False
