{
    'name': 'IDA Sales Approval',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Multi-level approval workflow for Sales Quotations',
    'description': """
        Adds a configurable multi-level approval workflow to Sales Quotations.
        - Enable/disable approval from Sales Configuration
        - Define approval levels with multiple approvers per level
        - Quotations must pass all approval levels before confirmation
        - Approvers are notified via the chatter
    """,
    'author': 'Joshua Aclan',
    'depends': ['sale_management'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/sale_approval_refuse_wizard_views.xml',
        'views/sale_approval_level_views.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
