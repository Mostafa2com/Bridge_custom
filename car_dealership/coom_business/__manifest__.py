{
    'name': '2CooM Car Dealership Business',

    'description': "Module helps you improve you business COA to detect common mistakes that can be done on the COA",
    'author': '2CooM',
    'depends': ['base',
                'sale',
                'stock',
                'account',
                'sale_order_lot_selection'],
    'data': ['views/stock_lot.xml',
             'views/account_move.xml',
             'views/report_invoice.xml',
             'views/sale_view.xml',
            'views/stock_move_line.xml',

             ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
