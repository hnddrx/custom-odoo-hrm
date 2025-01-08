# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Employee Info Update',
    'version': '0.1',
    'summary': 'Custom Lotus Employees',
    'category': 'Application Management',
    'description': """ 
    Custom Lotus Employees
    """,
    'depends': [
        'base',
        'hr',
        'workflow'
    ],
    'data': [
        'data/info_update.xml',
        'security/ir.model.access.csv',
        'views/update_info_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': '',
}
