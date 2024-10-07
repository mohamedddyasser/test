{
    "name": "Intalio Sale Document Checklist",
    "summary": "Intalio Sale Document Checklist",
    "category": "Intalio",
    "version": "17.0.0.0.0",
    "description": """
    List of require document option will be added in sales order before user create any invoice from SO .
    """,
    "author": "Intalio, Hazem Essam El-DIN",
    "maintainer": "Intalio, Hazem Essam El-DIN",
    "website": "https://www.intalio.com",
    "depends": ["sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
    ],
    "license": "LGPL-3",
}
