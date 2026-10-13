{
    "name": "BSOFT Kitchen Display",
    "summary": "Pantalla de cocina Kanban para Odoo 17 Community",
    "version": "17.0.2.0.0",
    "category": "Point of Sale",
    "author": "BSOFT Consulting",
    "website": "https://www.bsoftconsulting.com.mx",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "pos_restaurant", "bus"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/kitchen_station_views.xml",
        "views/kitchen_display_menus.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "bsoft_kitchen_display/static/src/js/kitchen_display.js",
            "bsoft_kitchen_display/static/src/xml/kitchen_display.xml",
            "bsoft_kitchen_display/static/src/scss/kitchen_display.scss"
        ]
    },
    "installable": True,
    "application": True,
    "post_init_hook": "post_init_hook",
}
