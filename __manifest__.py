# -*- coding: utf-8 -*-
################################################################################
#
#    Guidasworld Ltd. (https://www.guidasworld.com)
#    Author: GUIGUI David (<https://www.guidasworld.com>)
#
################################################################################
{
    "name": "Email OTP Authentication",
    "version": "0.1",
    "author": "GUIGUI David",
    "sequence": 2,
    "website": "https://www.guidasworld.com/",
    'category': 'Tools/OTP',
    "description": """
        """,
    "summary": """
        This module allows the user authentication of the database via OTP.
    """,
    'depends': ['base', 'mail', 'web', 'website', 'auth_signup', "portal"],
    'data': [
        "security/ir.model.access.csv",
        "security/security_group.xml",
        "views/otp_verification.xml",
        "views/login_view.xml",
        "views/otp_signup.xml",
        "data/cron.xml",
    ],

    'assets': {
        'web.assets_frontend': [
            'otp_login/static/src/js/signup_password_toggle.js',
            'otp_login/static/src/js/validate_password.js',
            'otp_login/static/src/js/login_otp.js',
            'otp_login/static/src/js/signup_otp.js',
        ],
    },

    "price": 0,
    "currency": "USD",
    "license": "LGPL-3",
    'installable': True,
    'application': True,
    'images': ['static/description/banner.png']
}
