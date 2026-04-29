from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _timesheet_create_project_prepare_values(self):
        """Set the project name to the base project number while projects are
        being created inside _action_confirm(), before the sub-sequence index
        is applied in SaleOrder.action_confirm()."""
        values = super()._timesheet_create_project_prepare_values()
        order = self.order_id
        if order.deal_type == 'new_project' and order.base_project_number:
            product_name = self.product_id.name or ''
            suffix = f" {product_name}" if product_name else ''
            values['name'] = f"{order.base_project_number}"
        return values
