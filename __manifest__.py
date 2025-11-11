{
    'name': 'Export TXT RET/PER SIRCAR Misiones',
    'license': 'AGPL-3',
    'author': 'ADHOC SA, Moldeo Interactive, Exemax, Codize',
    'category': 'Accounting & Finance',
    'data': [
        'views/account_export_sircar_misiones_view.xml',
        'views/res_partner_view.xml',
        'views/account_tax_inherit_view.xml',
        'views/res_company_view.xml',
        'security/ir.model.access.csv',
    ],
    'depends': [
        'base',
        'contacts',
        'account',
        'l10n_ar',
        
        #'l10n_ar_withholding',
        'l10n_ar_sircar_regimenes',
    ],
    'installable': True,
    'version': '18.0.1.0.0',
}
