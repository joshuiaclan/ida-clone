from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _timesheet_create_project_prepare_values(self):
        """Set the project name to the base project number while projects are
        being created inside _action_confirm(), before the sub-sequence index
        is applied in SaleOrder.action_confirm()."""
        values = super()._timesheet_create_project_prepare_values()
        order = self.order_id
        if order.base_project_id and order.deal_type in ('new_project', 'existing_project'):
            values['name'] = order.base_project_id.number
        return values

    def _timesheet_create_project(self):
        """Skip project creation entirely for additional_services orders.

        The SO is connected to an existing base project; no new subproject
        should be created regardless of the product's service_tracking setting.
        """
        if self.order_id.deal_type == 'additional_services':
            return self.env['project.project']
        return super()._timesheet_create_project()

    def _timesheet_create_task(self, project):
        """Skip task creation entirely for additional_services orders."""
        if self.order_id.deal_type == 'additional_services':
            return self.env['project.task']
        return super()._timesheet_create_task(project)
