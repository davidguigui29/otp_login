# -*- coding: utf-8 -*-
from odoo import _
import logging

_logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# CSS THEMES
# -------------------------------------------------------------------------
EMAIL_THEMES = {
    "classic": """
        body {
            margin: 0; padding: 0;
            background-color: #f9f9f9;
            font-family: Arial, sans-serif;
            color: #333;
        }
        .wrapper {
            width: 600px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        .header {
            background-color: #004080;
            color: #fff;
            text-align: center;
            padding: 20px;
        }
        .header img {
            height: 50px;
            margin-bottom: 10px;
        }
        .content {
            padding: 30px;
            font-size: 15px;
            line-height: 1.7;
            color: #444;
        }
        .otp-badge {
            text-align: center;
            margin: 20px 0;
        }
        .otp-badge span {
            font-size: 22px;
            font-weight: bold;
            color: #004080;
            padding: 12px 25px;
            border: 2px dashed #004080;
            border-radius: 6px;
            display: inline-block;
        }
        .footer {
            background-color: #f1f1f1;
            font-size: 12px;
            color: #777;
            text-align: center;
            padding: 15px;
        }
        a {
            color: #004080;
            text-decoration: none;
        }
    """,

    "modern-dark": """
        body {
            margin: 0;
            padding: 0;
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #121212 0%, #1a1a40 50%, #0f2027 100%) fixed;
            color: #f8f9fa;
        }
        .wrapper {
            width: 600px;
            margin: 30px auto;
            background: rgba(30, 30, 47, 0.9);
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(6px);
        }
        .header {
            text-align: center;
            padding: 25px;
            background: linear-gradient(45deg, #6a11cb, #2575fc);
            color: #fff;
        }
        .header img {
            height: 55px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .content {
            padding: 35px 30px;
            font-size: 15px;
            color: #ddd;
        }
        .otp-badge {
            text-align: center;
            margin: 25px 0;
        }
        .otp-badge span {
            font-size: 26px;
            font-weight: bold;
            padding: 14px 28px;
            border-radius: 10px;
            display: inline-block;
            background: linear-gradient(45deg, #6a11cb, #2575fc);
            color: #fff;
            box-shadow: 0 0 15px rgba(100, 100, 255, 0.4);
        }
        .footer {
            text-align: center;
            padding: 18px;
            background: rgba(255, 255, 255, 0.05);
            font-size: 13px;
            color: #aaa;
        }
        a {
            color: #5f3dc4;
            text-decoration: none;
        }
    """,

    "neogreen": """
        body {
            margin: 0;
            padding: 0;
            background-color: #f4f6f5;
            font-family: 'Poppins', sans-serif;
            color: #2e2e2e;
        }
        .wrapper {
            width: 600px;
            margin: 25px auto;
            background: #ffffff;
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(90deg, #00a651, #00843d);
            color: #fff;
            text-align: center;
            padding: 30px 25px;
        }
        .header img {
            height: 60px;
            margin-bottom: 8px;
            border-radius: 8px;
            background: #fff;
            padding: 8px;
        }
        .content {
            padding: 35px 30px;
            line-height: 1.8;
            font-size: 15px;
        }
        .content p {
            margin-bottom: 18px;
        }
        .otp-badge {
            text-align: center;
            margin: 30px 0;
        }
        .otp-badge span {
            background: linear-gradient(90deg, #00a651, #00843d);
            color: #fff;
            font-size: 28px;
            font-weight: 600;
            padding: 14px 32px;
            border-radius: 10px;
            display: inline-block;
            letter-spacing: 2px;
            box-shadow: 0 4px 10px rgba(0, 166, 81, 0.3);
        }
        .footer {
            text-align: center;
            background: #f0f0f0;
            color: #555;
            padding: 18px;
            font-size: 13px;
            border-top: 1px solid #e0e0e0;
        }
        a {
            color: #00a651;
            text-decoration: none;
            font-weight: 500;
        }
    """,
}




# -------------------------------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------------------------------
def otp_login_html(company_logo, company_name, name, otp_code, company_phone, company_website, view_look="classic"):
    """
    Returns the full HTML email body for login/OTP verification.
    Supports multiple modern CSS looks defined in EMAIL_THEMES.
    """
    css_style = EMAIL_THEMES.get(view_look, EMAIL_THEMES["classic"])
    _logger.debug("Generating signup HTML with look: %s", view_look)

    logo_html = f"<img src='{company_logo}' alt='{company_name}'>" if company_logo else ""

    body_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{css_style}</style>
    </head>
    <body>
        <div class="wrapper">
            <div class="header">
                {logo_html}
                <h2>{company_name}</h2>
            </div>

            <div class="content">
                <p>Dear <b>{name}</b>,</p>
                <p>
                    To complete your login to <b>{company_name}</b>, please use the OTP below:
                </p>

                <div class="otp-badge">
                    <span>{otp_code}</span>
                </div>

                <p>
                    ⚠️ This OTP will expire shortly. If you did not initiate this registration, please ignore this email.
                </p>

                <p style="margin-top:30px;">Best regards,<br><b>{company_name} Security Team</b></p>
            </div>

            <div class="footer">
                <p>
                    {company_name}
                    <a href="{company_website}">{company_website}</a>
                </p>
                <p>&copy; {company_name} - All Rights Reserved</p>
            </div>
        </div>
    </body>
    </html>
    """
    return body_html



def otp_signup_html(company_logo, company_name, name, otp_code, company_phone, company_website, view_look="classic"):
    """
    Returns the full HTML email body for signup/OTP verification.
    Supports multiple modern CSS looks defined in EMAIL_THEMES.
    """
    css_style = EMAIL_THEMES.get(view_look, EMAIL_THEMES["classic"])
    _logger.debug("Generating signup HTML with look: %s", view_look)

    logo_html = f"<img src='{company_logo}' alt='{company_name}'>" if company_logo else ""

    body_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{css_style}</style>
    </head>
    <body>
        <div class="wrapper">
            <div class="header">
                {logo_html}
                <h2>{company_name}</h2>
            </div>

            <div class="content">
                <p>Dear <b>{name}</b>,</p>
                <p>
                    Welcome to <b>{company_name}</b>! Please verify your email by entering the OTP below.
                </p>

                <div class="otp-badge">
                    <span>{otp_code}</span>
                </div>

                <p>
                    ⚠️ This OTP will expire shortly. If you did not initiate this registration, please ignore this email.
                </p>

                <p style="margin-top:30px;">Best regards,<br><b>{company_name} Team</b></p>
            </div>

            <div class="footer">
                <p>
                    {company_name}
                    <a href="{company_website}">{company_website}</a>
                </p>
                <p>&copy; {company_name} - All Rights Reserved</p>
            </div>
        </div>
    </body>
    </html>
    """
    return body_html
