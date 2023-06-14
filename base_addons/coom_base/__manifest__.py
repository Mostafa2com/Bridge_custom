{
    'name': 'IfrsERP Base',

    'description': "Module helps you improve you business COA to detect common mistakes that can be done on the COA",
    'author': 'IfrsERP',
    'depends': ['account' ,
                'sale',
                'stock'],
    'data': ['views/res_config_settings_views.xml',
             'views/hr_job.xml'
             ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
