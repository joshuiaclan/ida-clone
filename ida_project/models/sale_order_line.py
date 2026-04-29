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
