{
    'name': 'IDA Sales',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Sales Order Customization — Project Classification Fields',
    'description': """
        Adds project classification fields to Sales Orders:
        - New Project: auto-generates a base project number on confirmation
        - Existing Project: requires selection of an existing base project
        - Additional Services: marks the order as additional services for a client
    """,
    'author': 'IDA',
    'depends': [
        'sale_management',
        'project',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
