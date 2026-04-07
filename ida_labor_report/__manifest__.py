{
    'name': 'IDA Labor Report',
    'version': '19.0.1.0.0',
    'category': 'Project/Reporting',
    'summary': 'Contracted Labor Cost vs. Labor Cost Billed with personnel efficiency analysis',
    'author': 'Joshua Aclan',
    'depends': [
        'hr_timesheet',
        'project',
        'sale_management',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/ida_labor_report_template.xml',
        'views/ida_labor_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
