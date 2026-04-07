from odoo import models, fields, api
from collections import defaultdict


class IdaLaborReport(models.TransientModel):
    _name = 'ida.labor.report'
    _description = 'Labor Cost Report Wizard'

    date_from = fields.Date(
        string='From',
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )
    date_to = fields.Date(
        string='To',
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )
    project_ids = fields.Many2many(
        comodel_name='project.project',
        string='Projects',
        help='Leave empty to include all projects.',
    )
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Employees',
        help='Leave empty to include all employees.',
    )

    # ── Data helpers ─────────────────────────────────────────────────────────

    def _timesheet_domain(self):
        domain = [
            ('project_id', '!=', False),
            ('employee_id', '!=', False),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids.ids))
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        return domain

    def _get_contracted_amounts(self, project_ids):
        """Return {project_id: contracted_amount} from confirmed sale orders."""
        if not project_ids:
            return {}
        lines = self.env['sale.order.line'].search([
            ('project_id', 'in', list(project_ids)),
            ('order_id.state', 'in', ['sale', 'done']),
        ])
        result = defaultdict(float)
        for line in lines:
            result[line.project_id.id] += line.price_subtotal
        return dict(result)

    def _get_billed_amounts(self, project_ids):
        """Return {project_id: billed_amount} from posted customer invoices,
        resolved via sale order line → project link."""
        if not project_ids:
            return {}
        sol = self.env['sale.order.line'].search([
            ('project_id', 'in', list(project_ids)),
        ])
        if not sol:
            return {}
        aml = self.env['account.move.line'].search([
            ('sale_line_ids', 'in', sol.ids),
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
            ('move_id.state', '=', 'posted'),
            ('display_type', '=', 'product'),
        ])
        result = defaultdict(float)
        for line in aml:
            for sol_line in line.sale_line_ids:
                if sol_line.project_id:
                    sign = -1 if line.move_id.move_type == 'out_refund' else 1
                    result[sol_line.project_id.id] += sign * line.price_subtotal
        return dict(result)

    # ── Main report data builder ──────────────────────────────────────────────

    def _get_report_values(self):
        """Build all data consumed by the QWeb template.

        Returns a list of project dicts, each containing:
          - project       : project.project record
          - employees     : list of per-employee dicts
          - total_hours   : float
          - total_cost    : float   (Σ hours × employee rate)
          - contracted    : float   (from sale order lines)
          - billed        : float   (from posted invoices)
          - variance      : float   (billed − total_cost)
          - efficiency    : float   (billed / total_cost × 100, or 0)
        """
        groups = self.env['account.analytic.line'].read_group(
            domain=self._timesheet_domain(),
            fields=['project_id', 'employee_id', 'unit_amount:sum'],
            groupby=['project_id', 'employee_id'],
            lazy=False,
        )

        # Collect all project ids present in timesheets
        project_ids = {g['project_id'][0] for g in groups if g.get('project_id')}
        contracted_map = self._get_contracted_amounts(project_ids)
        billed_map = self._get_billed_amounts(project_ids)

        # Pre-fetch employee timesheet costs
        employee_ids = {g['employee_id'][0] for g in groups if g.get('employee_id')}
        employees = self.env['hr.employee'].browse(list(employee_ids))
        rate_map = {e.id: e.timesheet_cost or 0.0 for e in employees}

        # Aggregate per project
        projects_map = {}
        for g in groups:
            if not g.get('project_id') or not g.get('employee_id'):
                continue
            project_id = g['project_id'][0]
            employee_id = g['employee_id'][0]
            hours = g['unit_amount'] or 0.0
            rate = rate_map.get(employee_id, 0.0)
            cost = hours * rate

            if project_id not in projects_map:
                projects_map[project_id] = {
                    'project': self.env['project.project'].browse(project_id),
                    'employees': [],
                    'total_hours': 0.0,
                    'total_cost': 0.0,
                }
            projects_map[project_id]['employees'].append({
                'employee': self.env['hr.employee'].browse(employee_id),
                'rate': rate,
                'hours': hours,
                'cost': cost,
            })
            projects_map[project_id]['total_hours'] += hours
            projects_map[project_id]['total_cost'] += cost

        # Attach financial figures and efficiency metrics
        for pid, data in projects_map.items():
            contracted = contracted_map.get(pid, 0.0)
            billed = billed_map.get(pid, 0.0)
            total_cost = data['total_cost']
            data['contracted'] = contracted
            data['billed'] = billed
            data['variance'] = billed - total_cost
            data['efficiency'] = (billed / total_cost * 100.0) if total_cost else 0.0

        projects = sorted(projects_map.values(), key=lambda p: p['project'].name or '')

        # Grand totals
        grand = {
            'total_hours': sum(p['total_hours'] for p in projects),
            'total_cost': sum(p['total_cost'] for p in projects),
            'contracted': sum(p['contracted'] for p in projects),
            'billed': sum(p['billed'] for p in projects),
        }
        grand['variance'] = grand['billed'] - grand['total_cost']
        grand['efficiency'] = (
            grand['billed'] / grand['total_cost'] * 100.0
            if grand['total_cost'] else 0.0
        )

        return {
            'docs': self,
            'wizard': self,
            'projects': projects,
            'grand': grand,
            'currency': self.env.company.currency_id,
        }

    def action_print_report(self):
        self.ensure_one()
        return self.env.ref('ida_labor_report.action_report_ida_labor').report_action(self)


class IdaLaborReportHandler(models.AbstractModel):
    """QWeb report data provider — name must match the template id."""
    _name = 'report.ida_labor_report.ida_labor_report_template'
    _description = 'Labor Report QWeb Handler'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['ida.labor.report'].browse(docids)
        return wizard._get_report_values()
