{
    'name': 'IDA Accounting',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Accounting Customization — Analytic Distribution Enhancements',
    'description': """
        - Extends the Analytic Distribution popup on Journal Items to display
          a computed Amount column alongside each distribution line's percentage.
        - Automatically propagates the analytic distribution set on an invoice's
          AR/AP line to the corresponding payment journal entry line upon reconciliation.
    """,
    'author': 'Joshua Aclan',
    'depends': [
        'account',
        'analytic',
    ],
    'assets': {
        'web.assets_backend': [
            'ida_accounting/static/src/components/analytic_distribution_amount/analytic_distribution_amount.js',
            'ida_accounting/static/src/components/analytic_distribution_amount/analytic_distribution_amount.xml',
            'ida_accounting/static/src/components/analytic_distribution_amount/analytic_distribution_amount.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
