{
    'name': "My library",
    'summary': "Manage books easily",
    'description': """Long description""",
    'author': "sparta",
    'website': "http://www.example.com",
    'category': 'Library',
    'version': '13.0.1',
    'depends': ['base','product','base_setup', 'contacts', 'website', 'utm', 'web'],
    'data': ['security/groups.xml',
             'security/ir.model.access.csv',
             'security/library_security.xml',
             'views/library_book.xml',
             'views/library_book_categ.xml',
             'views/library_book_member.xml',
             'views/library_book_rent.xml',
             'views/library_book_rent_wizard.xml',
             'views/library_book_return_wizard.xml',
             'views/library_book_statistics.xml',
             'views/res_config_settings_views.xml',
             'views/templates.xml',
             'views/snippets.xml',
             'data/data.xml',
             'data/library_stage.xml',
             'reports/book_rent_templates.xml',
             'reports/book_rent_report.xml'
             ],
    'post_init_hook': 'add_book_hook',
    'demo': [ 
        'demo/demo.xml', 
    ],
    'qweb': [
        'static/src/xml/qweb_template.xml'
    ],
}

# 'demo': ['demo.xml'],
