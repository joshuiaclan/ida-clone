from odoo import fields, http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal


class IdaSalesPortal(CustomerPortal):

    @http.route(
        '/my/orders/<int:order_id>/accept_terms',
        type='http',
        auth='public',
        methods=['POST'],
        website=True,
    )
    def portal_accept_terms(self, order_id, access_token=None, **post):
        """Handle Agreement Acceptance form submission from the customer portal."""
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # accepted_signature arrives as a base64-encoded PNG string from the
        # canvas widget; Odoo Binary fields store values as raw base64.
        signature_b64 = (post.get('accepted_signature') or '').strip()

        vals = {
            'accepted_printed_name':   (post.get('accepted_printed_name')   or '').strip(),
            'accepted_email':          (post.get('accepted_email')          or '').strip(),
            'accepted_title':          (post.get('accepted_title')          or '').strip(),
            'accepted_date':           fields.Date.today(),
            'accepted_legal_entity':   (post.get('accepted_legal_entity')   or '').strip(),
            'accepted_entity_address': (post.get('accepted_entity_address') or '').strip(),
            'accepted_invoice_email':  (post.get('accepted_invoice_email')  or '').strip(),
        }
        if signature_b64:
            vals['accepted_signature'] = signature_b64

        order_sudo.sudo().write(vals)

        return request.redirect(order_sudo.get_portal_url())
