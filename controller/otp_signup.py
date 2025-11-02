

import logging
import re
import string
from random import choice

from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OtpSignupHome(AuthSignupHome):
    """Custom Signup Controller with OTP verification."""

    # --------------------------------------------------
    # Utility helpers
    # --------------------------------------------------

    def _build_otp_email(self, email, name, otp_code):
        """Return subject, body_html for OTP email."""
        company = request.env.company
        email_from = company.email or "noreply@example.com"
        company_name = company.name or "Your Company"
        # company_logo = f"/web/image/res.company/{company.id}/logo" if company.logo else ""
        company_logo = ""
        if company.logo:
            base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
            company_logo = f"{base_url}/web/image/res.company/{company.id}/logo"
        company_website = company.website or "#"
        company_phone = company.phone or "N/A"

        subject = _(f"[{company_name}] Verify Your Account - OTP Required")

        body_html = f"""
        <html>
        <body style="margin:0; padding:0; background-color:#f9f9f9; font-family:Arial, sans-serif; color:#333;">
            <table align="center" width="600" cellpadding="0" cellspacing="0" 
                style="margin:20px auto; background:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08);">

                <!-- Header -->
                <tr style="background-color:#004080; color:#ffffff;">
                    <td style="padding:20px; text-align:center;">
                        {f"<img src='{company_logo}' alt='{company_name}' height='50' style='margin-bottom:10px;'>" if company_logo else ""}
                        <span style="font-size:20px; font-weight:bold; letter-spacing:1px;">{company_name}</span>
                    </td>
                </tr>

                <!-- Body -->
                <tr>
                    <td style="padding:30px; font-size:15px; line-height:1.7; color:#444;">
                        <p>Dear <b>{name}</b>,</p>
                        <p>
                            Welcome to <b>{company_name}</b>! To complete your signup process, please confirm your account using the OTP below.
                        </p>

                        <!-- OTP badge -->
                        <p style="text-align:center; margin:20px 0;">
                            <span style="font-size:22px; font-weight:bold; color:#004080; padding:12px 25px; 
                                        border:2px dashed #004080; border-radius:6px; display:inline-block;">
                                {otp_code}
                            </span>
                        </p>

                        <p>
                            ⚠️ This OTP will expire shortly. Please use it as soon as possible.<br>
                            If you did not create an account with us, kindly ignore this email.
                        </p>

                        <p style="margin-top:30px;">Warm regards,<br><b>{company_name} Team</b></p>
                    </td>
                </tr>

                <!-- Footer -->
                <tr style="background-color:#f1f1f1; font-size:12px; color:#777;">
                    <td style="padding:15px; text-align:center;">
                        <p>
                            {company_name} | {company_phone} | 
                            <a href="{company_website}" style="color:#004080; text-decoration:none;">{company_website}</a>
                        </p>
                        <p>&copy; {company_name} - All Rights Reserved</p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        return subject, email_from, body_html

    def _send_otp_email(self, email, name, otp_code):
        """Build and send OTP email."""
        subject, email_from, body_html = self._build_otp_email(email, name, otp_code)
        mail = request.env['mail.mail'].sudo().create({
            'subject': subject,
            'email_from': email_from,
            'email_to': email,
            'body_html': body_html,
        })
        mail.send()
        return mail




    def _is_valid_password(self, password):
        """Validate password complexity rules."""
        if not password:
            return False
        if len(password) < 8 or len(password) > 20:
            return False
        if not re.search(r"[A-Z]", password):  # uppercase
            return False
        if not re.search(r"[a-z]", password):  # lowercase
            return False
        if not re.search(r"\d", password):  # digit
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=;']", password):  # symbol
            return False
        return True



    def generate_otp(self, number_of_digits):
        otp = ''.join(choice(string.digits) for _ in range(number_of_digits))
        _logger.info("Generated OTP: %s", otp)
        return otp



    # --------------------------------------------------
    # OTP Step 1: Initial signup (send OTP)
    # --------------------------------------------------
    @http.route('/web/signup/otp', type='http', auth='public', website=True, sitemap=False)
    def web_signup_otp(self, **kw):
        qcontext = request.params.copy()
        # _logger.info("Signup step 1 - raw params: %s", qcontext)

        # qcontext = self._ensure_name_in_qcontext(qcontext)
        # _logger.info("Signup step 1 - processed qcontext: %s", qcontext)


        # Validate passwords
        password = qcontext.get("password")
        confirm_password = qcontext.get("confirm_password")

        if not (password and password == confirm_password):
            qcontext["error"] = _("Passwords do not match, please retype them.")
            return request.render('otp_login.custom_otp_signup', qcontext)

        # Check password complexity
        if not self._is_valid_password(password):
            qcontext["error"] = _(
                "Password must be 8–20 characters long and include at least: "
                "one uppercase letter, one lowercase letter, one number, and one special character."
            )
            return request.render('otp_login.custom_otp_signup', qcontext)

        # Check if user already exists
        if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
            qcontext["error"] = _("Another user is already registered using this email address.")
            return request.render('otp_login.custom_otp_signup', qcontext)

        # Generate OTP
        otp_code = self.generate_otp(4)
        email = str(qcontext.get('login'))
        name = str(qcontext.get('name'))

        self._send_otp_email(email, name, otp_code)

        # # Confirmation link (optional, can include OTP or a token)
        # # confirmation_link = request.httprequest.host_url + f"/web/signup/confirm?email={email}&otp={otp_code}"
        # # _logger.info("Confirmation link %s sent to email %s", confirmation_link, email)


        # Save OTP in custom model
        request.env['otp.verification'].sudo().create({
            'otp': otp_code,
            'email': email,
        })

        # _logger.info("OTP %s sent to email %s", otp_code, email)

        # Render OTP entry form
        return request.render('otp_login.custom_otp_signup', {
            'otp': True,
            'otp_login': True,
            'login': qcontext["login"],
            'otp_no': otp_code,
            'name': name,
            'password': qcontext["password"],
            'confirm_password': qcontext["confirm_password"],
        })

    # --------------------------------------------------
    # OTP Step 2: Verify OTP and create user
    # --------------------------------------------------
    @http.route('/web/signup/otp/verify', type='http', auth='public', website=True, sitemap=False)
    def web_otp_signup_verify(self, *args, **kw):
        qcontext = request.params.copy()
        # qcontext = self._ensure_name_in_qcontext(qcontext)

        # _logger.info("Signup step 2 - verify route qcontext: %s", qcontext)

        email = str(qcontext.get('login'))
        otp_input = str(qcontext.get('otp'))
        password = qcontext.get('password')
        confirm_password = qcontext.get('confirm_password')

        res_id = request.env['otp.verification'].search([('email', '=', email)], order="create_date desc", limit=1)
        otp_stored = res_id.otp if res_id else None

        try:
            if otp_stored and otp_input == otp_stored:
                res_id.state = 'verified'
                _logger.info("OTP verified successfully for email %s", email)
                return self.web_auth_signup(*args, **kw)
            else:
                if res_id:
                    res_id.state = 'rejected'
                # _logger.warning("OTP verification failed for email %s. Entered: %s, Expected: %s",
                #                 email, otp_input, otp_stored)
                return request.render('otp_login.custom_otp_signup', {
                    'otp': True,
                    'otp_login': True,
                    'login': email,
                    'name': qcontext["name"],
                    'password': password,
                    'confirm_password': confirm_password,
                    'otp_error': True,
                })

        except UserError as e:
            qcontext['error'] = e.name or e.value
            _logger.error("UserError during OTP verification: %s", e)

        return request.render('otp_login.custom_otp_signup', {
            'otp': True,
            'otp_login': True,
            'login': email,
            'name': qcontext.get("name"),
            'password': password,
            'confirm_password': confirm_password,
        })


    @http.route('/web/signup/otp/resend', type='json', auth='public', website=True, csrf=False)
    def web_signup_otp_resend(self, **kw):
        data = request.get_json_data()
        qcontext = request.params.copy()

        email = data.get("login")
        name = data.get("name", "User")



        # _logger.info(f"Resend OTP request for: {email} and name: {name}")
        # _logger.info(f"Resend OTP raw data: {data}")


        if not email:
            return {"status": "error", "message": "Missing email"}


        # user_id = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)

        # Generate OTP
        OTP = self.generate_otp(4)
        _logger.info(f"Resent OTP for {email}: {OTP}")

        # Save OTP
        request.env['otp.verification'].sudo().create({
            "otp": OTP,
            "email": email
        })

        
        self._send_otp_email(email, name, otp_code=OTP)

        return {"status": "success", "message": "OTP resent successfully"}
