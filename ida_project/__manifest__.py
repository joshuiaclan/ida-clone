{
    'name': 'IDA Project',
    'version': '19.0.1.0.0',
    'category': 'Project',
    'summary': 'Structured project number generation from confirmed Sales Orders',
    'description': """
        Generates a fully-structured Base Project Number when a Sales Order
        with Project Type = "New Project" is confirmed.

        Number format:  {YEAR}-{DEPT_CODE}-{SEQ}-{LOC_SEQ}
        Example:        2026-IT-001-01

        Components
        ──────────
        YEAR      – 4-digit confirmation year
        DEPT_CODE – department_short_code from the first product on the
                    sale order lines that has the field populated
        SEQ       – 3-digit yearly-reset sequence (Odoo ir.sequence,
                    resets to 001 on 1 January each year)
        LOC_SEQ   – 2-digit count of New-Project orders confirmed at the
                    same Project Location in the same year (the "final
                    suffix added in the backend at generation time")

        The generated number is written to the project.project *name*
        field (no separate field needed on the project model).
    """,
    'author': 'Joshua Aclan',
    'depends': [
        'sale_management',
        'sale_project',
        'project',
        'product',
        'ida_sales',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/ida_project_location_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/project_project_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
