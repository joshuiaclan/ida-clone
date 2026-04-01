{
    'name': 'IDA Time Off',
    'version': '19.0.1.0.0',
    'category': 'Time Off',
    'summary': 'Adds Unpaid Time Off Type classification to time off requests',
    'author': 'Joshua Aclan',
    'depends': [
        'hr_holidays',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ida_unpaid_leave_type_views.xml',
        'views/hr_holiday_status_views.xml',
        'views/hr_leave_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
