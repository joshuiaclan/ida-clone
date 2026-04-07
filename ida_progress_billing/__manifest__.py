{
    'name': 'IDA Progress Billing',
    'version': '19.0.1.0.0',
    'category': 'Sales/Accounting',
    'summary': 'Progress billing on sale orders and invoices based on percent complete',
    'author': 'Joshua Aclan',
    'depends': [
        'sale_management',
        'account',
    ],
    'data': [
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'report/report_invoice.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
