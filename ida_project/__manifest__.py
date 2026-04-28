{
    'name': 'IDA Project',
    'version': '19.0.1.0.0',
    'category': 'Project',
    'summary': 'Structured project number generation on sale order confirmation',
    'author': 'Joshua Aclan',
    'depends': [
        'ida_sales',
        'sale_project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/ida_base_project_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
