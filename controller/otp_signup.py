

import logging
import re
import string
from random import choice

from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError
from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.otp_login.utils.email_templates import otp_signup_html



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
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        company_logo = ""
        if company.logo:
            company_logo = f"{base_url}/web/image/res.company/{company.id}/logo"
        company_website = company.website or "#"
        company_phone = company.phone or "N/A"

        subject = _(f"[{company_name}] Verify Your Account - OTP Required")

        body_html = otp_signup_html(company_logo=company_logo, company_name=company_name, name=name, otp_code=otp_code, company_phone=company_phone, company_website=company_website, view_look="neogreen")
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


    def _get_oauth_providers(self):
        """Get real OAuth providers to show on signup page."""
        try:
            return OAuthLogin().list_providers()
        except Exception as e:
            _logger.warning("Failed to load OAuth providers: %s", e)
            return []




    # --------------------------------------------------
    # OTP Step 1: Initial signup (send OTP)
    # --------------------------------------------------
    @http.route('/web/signup/otp', type='http', auth='public', website=True, sitemap=False)
    def web_signup_otp(self, **kw):
        qcontext = request.params.copy()

        # Include OAuth providers
        qcontext['providers'] = self._get_oauth_providers()

        password = qcontext.get("password")
        confirm_password = qcontext.get("confirm_password")

        if not (password and password == confirm_password):
            qcontext["error"] = _("Passwords do not match, please retype them.")
            return request.render('otp_login.custom_otp_signup', qcontext)

        if not self._is_valid_password(password):
            qcontext["error"] = _(
                "Password must be 8–20 characters long and include at least: "
                "one uppercase letter, one lowercase letter, one number, and one special character."
            )
            return request.render('otp_login.custom_otp_signup', qcontext)

        if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
            qcontext["error"] = _("Another user is already registered using this email address.")
            return request.render('otp_login.custom_otp_signup', qcontext)

        otp_code = self.generate_otp(4)
        email = str(qcontext.get('login'))
        name = str(qcontext.get('name'))

        self._send_otp_email(email, name, otp_code)

        request.env['otp.verification'].sudo().create({
            'otp': otp_code,
            'email': email,
        })

        return request.render('otp_login.custom_otp_signup', {
            'otp': True,
            'otp_login': True,
            'login': email,
            'otp_no': otp_code,
            'name': name,
            'password': password,
            'confirm_password': confirm_password,
            'providers': self._get_oauth_providers(),  # include real OAuth
        })

    # --------------------------------------------------
    # OTP Step 2: Verify OTP and create user
    # --------------------------------------------------
    @http.route('/web/signup/otp/verify', type='http', auth='public', website=True, sitemap=False)
    def web_otp_signup_verify(self, *args, **kw):
        qcontext = request.params.copy()
        qcontext['providers'] = self._get_oauth_providers()

        email = str(qcontext.get('login'))
        otp_input = str(qcontext.get('otp'))
        password = qcontext.get('password')
        confirm_password = qcontext.get('confirm_password')

        res_id = request.env['otp.verification'].sudo().search(
            [('email', '=', email)], order="create_date desc", limit=1
        )
        otp_stored = res_id.otp if res_id else None

        try:
            if otp_stored and otp_input == otp_stored:
                res_id.state = 'verified'
                _logger.info("OTP verified successfully for email %s", email)
                return self.web_auth_signup(*args, **kw)
            else:
                if res_id:
                    res_id.state = 'rejected'
                return request.render('otp_login.custom_otp_signup', {
                    'otp': True,
                    'otp_login': True,
                    'login': email,
                    'name': qcontext.get("name"),
                    'password': password,
                    'confirm_password': confirm_password,
                    'otp_error': True,
                    'providers': self._get_oauth_providers(),
                })

        except UserError as e:
            qcontext['error'] = e.name or e.value
            _logger.error("UserError during OTP verification: %s", e)

        return request.render('otp_login.custom_otp_signup', qcontext)




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
        print(f"Here is your otp: {OTP}")
        _logger.info(f"Resent OTP for {email}: {OTP}")

        # Save OTP
        request.env['otp.verification'].sudo().create({
            "otp": OTP,
            "email": email
        })

        
        self._send_otp_email(email, name, otp_code=OTP)

        return {"status": "success", "message": "OTP resent successfully"}

