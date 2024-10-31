{
    'name': 'Certificate of Employment',
    'version': '1.0',
    'summary': 'This module is for managing Certificate of Employment',
    'description': 'A module to list and manage Certificate of Employment',
    'category': 'Human Resource',
    'author': 'Wren',
    'depends': [
        'base', 
        'web', 
        'hr',
        'base_setup',
        'resource',
        'web',
        'mail', 
        'advanced_movement',
        'advanced_employee_manager',
        'custom_approval_flow',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/certificate_of_employment.xml',
        'views/approval_flow.xml',
        'data/certificate_of_employment.xml',
        
    ], 
    "assets":{
        "web.assets_backend":[
            'certificate_of_employment/static/src/js/owl_component.js'
        ]
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3'
}