from odoo import http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


class OTPAuthSignup(AuthSignupHome):

    @http.route('/web/signup/otp', type='http', auth='public', website=True, csrf=False)
    def web_signup_otp(self, *args, **kwargs):
        # -----------------------------------
        # Server-side validation of T&C box
        # -----------------------------------
        if not kwargs.get("terms_conditions"):
            return request.render("otp_login.custom_otp_signup", {
                "error": "You must accept the Terms & Conditions to proceed.",
                "login": kwargs.get("login"),
                "name": kwargs.get("name"),
                "password": kwargs.get("password"),
                "confirm_password": kwargs.get("confirm_password"),
            })

        # Continue normal OTP logic
        return super(OTPAuthSignup, self).web_signup_otp(*args, **kwargs)
