from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _timesheet_create_project_prepare_values(self):
        """Use the pre-generated Base Project Number as the project name when
        the order is a New Project type and the number is already set."""
        values = super()._timesheet_create_project_prepare_values()
        order = self.order_id
        if order.project_type == 'new_project' and order.base_project_number:
            values['name'] = order.base_project_number
            if order.project_location_id:
                values['project_location_id'] = order.project_location_id.id
        return values
