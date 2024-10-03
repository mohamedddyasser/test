# -*- coding: utf-8 -*-
{
    'name': 'Base Advanced Approval',
    'summary': 'Allow to set advanced approval cycle',
    'author': 'Intalio EverTeam',
    'website': 'https://www.intalio.com/',
    'version': '17.0.1.0.0',
    'category': 'Hidden/Tools',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'resource',
    ],
    'data': [
        'security/ir_module_category.xml',
        'security/res_groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'wizards/approve_dynamic_approval_wizard.xml',
        'wizards/levels_dynamic_approval_wizard.xml',
        'wizards/reject_dynamic_approval_wizard.xml',
        'wizards/recall_dynamic_approval_wizard.xml',
        'views/dynamic_approval.xml',
        'views/dynamic_approval_role_views.xml',
        'views/dynamic_approval_request.xml',
        'views/ir_ui_menu.xml',
        'views/res_config_settings.xml',
        'views/mail_alias_views.xml',
        'data/mail_activity_type.xml',
        'data/ir_cron.xml',
        'data/ir_config_parameter.xml',
        "templates/tier_validation_templates.xml",
        'wizards/work_flow_select.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'base_dynamic_approval/static/src/xml/signature_widget.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,

}
