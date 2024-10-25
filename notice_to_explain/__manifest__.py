{
    'name': 'Employee Medical Record',
    'version': '1.0',
    'summary': 'This module is for managing Notice to explain',
    'description': 'A module to list and manage Notice to explain',
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
        'advanced_employee_manager',
        'custom_approval_flow',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/notice_to_explain.xml',
        'data/notice_to_explain.xml',
        
    ], 
    """ "assets":{
        "web.assets_backend":[
            'certificate_of_employment/static/src/js/counter/owl_component.js'
        ] 
    },  """
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}