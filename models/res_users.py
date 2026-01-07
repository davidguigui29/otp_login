# -*- coding: utf-8 -*-
from odoo import models, _, api, fields, SUPERUSER_ID
from odoo.http import request
from odoo.exceptions import ValidationError, AccessDenied
import re
import logging
import pytz

_logger = logging.getLogger(__name__)


def _check_password_strength(password):
    """
    Validate password against complexity rules.
    Returns (bool, message) so caller knows what failed.
    """
    if len(password) < 8:
        return False, _("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        return False, _("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        return False, _("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        return False, _("Password must contain at least one digit.")
    if not re.search(r"[@$!%*?&]", password):
        return False, _("Password must contain at least one special character (@, $, !, %, *, ?, &).")
    return True, None


class ResUsers(models.Model):
    _inherit = "res.users"



    terms_accepted = fields.Boolean(
        string="Terms & Conditions Accepted",
        default=False,
        help="Indicates whether the user accepted the Terms and Conditions during signup."
    )

    # -------------------------------------------------------------------------
    # LOGIN OVERRIDE
    # -------------------------------------------------------------------------

    @classmethod
    def _login(cls, db, credential, user_agent_env):
        ip = request.httprequest.environ.get("REMOTE_ADDR") if request else "n/a"
        login_value = credential.get("login")

        # 1. OAuth Bypass (Same as your current logic)
        if (request and "/auth_oauth/" in request.httprequest.path) or \
           (isinstance(credential, dict) and "oauth_provider_id" in credential):
            return super(ResUsers, cls)._login(db, credential, user_agent_env)

        if not login_value or not credential.get("password"):
            raise AccessDenied(_("Missing credentials."))

        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]

                with self._assert_can_auth():
                    # ✅ MODIFIED: Search by login OR by partner username
                    # First, try standard login
                    user = self.search(self._get_login_domain(login_value), limit=1)
                    
                    # Fallback: If not found, check if it's a 'username' on Myfansbook website
                    if not user and request and getattr(request, 'website', False) and \
                       request.website.name == 'Myfansbook':
                        
                        partner = self.env['res.partner'].search([('username', '=', login_value)], limit=1)
                        if partner:
                            user = self.search([('partner_id', '=', partner.id)], limit=1)

                    if not user:
                        raise AccessDenied(_("User not found."))

                    user = user.with_user(user)
                    cr.execute("SELECT COALESCE(password, '') FROM res_users WHERE id=%s", [user.id])
                    hashed = cr.fetchone()[0]

                    # OTP special case
                    if credential["password"] != hashed + "mobile_otp_login":
                        user._check_credentials(credential, user_agent_env)

                    # Update TZ and Last Login
                    tz = request.httprequest.cookies.get("tz") if request else None
                    if tz in pytz.all_timezones and (not user.tz or not user.login_date):
                        user.tz = tz
                    user._update_last_login()

        except AccessDenied:
            _logger.warning("Login failed for %s from %s", login_value, ip)
            raise

        _logger.info("Login successful for %s (UID %s) from %s", login_value, user.id, ip)
        return {"uid": user.id}
    # @classmethod
    # def _login(cls, db, credential, user_agent_env):
    #     """
    #     Custom login handler that supports:
    #     - Normal login with password
    #     - Mobile OTP login (password + 'mobile_otp_login' suffix)
    #     - OAuth login (delegated cleanly)
    #     """
    #     ip = request.httprequest.environ.get("REMOTE_ADDR") if request else "n/a"

    #     # ✅ 1. Detect OAuth login via route or credential
    #     if (
    #         request and "/auth_oauth/" in request.httprequest.path
    #     ) or (
    #         isinstance(credential, dict) and "oauth_provider_id" in credential
    #     ):
    #         _logger.info("Bypassing OTP for OAuth login from %s", ip)
    #         # Delegate directly to base class (do not enforce password)
    #         return super(ResUsers, cls)._login(db, credential, user_agent_env)

    #     # ✅ 2. Continue with normal or OTP-based password login
    #     if not isinstance(credential, dict) or "password" not in credential or not credential["password"]:
    #         _logger.warning("Login attempt missing password from %s", ip)
    #         raise AccessDenied(_("Missing password."))

    #     try:
    #         with cls.pool.cursor() as cr:
    #             self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]

    #             with self._assert_can_auth():
    #                 user = self.search(self._get_login_domain(credential["login"]),
    #                                 order=self._get_login_order(), limit=1)
    #                 if not user:
    #                     raise AccessDenied(_("User not found."))

    #                 user = user.with_user(user)

    #                 cr.execute("SELECT COALESCE(password, '') FROM res_users WHERE id=%s", [user.id])
    #                 hashed = cr.fetchone()[0]

    #                 # OTP special case
    #                 if credential["password"] != hashed + "mobile_otp_login":
    #                     user._check_credentials(credential, user_agent_env)

    #                 # Auto timezone update on first login
    #                 tz = request.httprequest.cookies.get("tz") if request else None
    #                 if tz in pytz.all_timezones and (not user.tz or not user.login_date):
    #                     user.tz = tz

    #                 user._update_last_login()

    #     except AccessDenied:
    #         _logger.warning("Login failed for %s from %s", credential.get("login"), ip)
    #         raise

    #     _logger.info("Login successful for %s from %s", credential.get("login"), ip)
    #     return {"uid": user.id}


    # # -------------------------------------------------------------------------
    # # PASSWORD STRENGTH ENFORCEMENT
    # # -------------------------------------------------------------------------
    # @api.model
    # def _check_password(self, password):
    #     """Enforce password strength globally."""
    #     valid, message = _check_password_strength(password)
    #     if not valid:
    #         _logger.warning("Weak password attempt for user %s: %s", self.id, message)
    #         raise ValidationError(message)
    #     return super(ResUsers, self)._check_password(password)

    # def change_password(self, old_password, new_password):
    #     """Override password change to validate complexity and confirmation."""
    #     confirm_password = (
    #         request.params.get("confirm_password") or request.params.get("new_password2")
    #     )
    #     if confirm_password and new_password != confirm_password:
    #         raise ValidationError(_("The new password and its confirmation do not match."))

    #     valid, message = _check_password_strength(new_password)
    #     if not valid:
    #         raise ValidationError(message)

    #     return super(ResUsers, self).change_password(old_password, new_password)



    # @classmethod
    # def _authenticate(cls, db, login, password, user_agent_env):
    #     try:
    #         # 1. Attempt standard Odoo authentication (Email/Login)
    #         return super(ResUsers, cls)._authenticate(db, login, password, user_agent_env)
    #     except AccessDenied:
    #         # 2. If standard fails, check if we are on "Myfansbook" and try Username login
    #         # We use a sudo environment to search across partners
    #         with cls.pool.cursor() as cr:
    #             env = api.Environment(cr, SUPERUSER_ID, {})
                
    #             # Check if the current website is Myfansbook
    #             # Note: 'request' is used to check the website context
    #             is_myfansbook = False
    #             if request and hasattr(request, 'website'):
    #                 is_myfansbook = request.website.name == 'Myfansbook'

    #             if is_myfansbook:
    #                 # Search for a partner with this username
    #                 partner = env['res.partner'].search([('username', '=', login)], limit=1)
    #                 if partner:
    #                     # Find the user linked to this partner
    #                     user = env['res.users'].search([('partner_id', '=', partner.id)], limit=1)
    #                     if user:
    #                         # Attempt to authenticate using the REAL login (email/phone) 
    #                         # stored in Odoo, but with the provided password
    #                         return super(ResUsers, cls)._authenticate(db, user.login, password, user_agent_env)
            
    #         # If all attempts fail, raise the original AccessDenied
    #         raise


# # -*- coding: utf-8 -*-
# from odoo import models, _, api, fields, SUPERUSER_ID
# from odoo.http import request
# from odoo.exceptions import ValidationError, AccessDenied
# import re
# import logging
# import pytz

# _logger = logging.getLogger(__name__)


# def _check_password_strength(password):
#     """
#     Validate password against complexity rules.
#     Returns (bool, message) so caller knows what failed.
#     """
#     if len(password) < 8:
#         return False, _("Password must be at least 8 characters long.")
#     if not re.search(r"[A-Z]", password):
#         return False, _("Password must contain at least one uppercase letter.")
#     if not re.search(r"[a-z]", password):
#         return False, _("Password must contain at least one lowercase letter.")
#     if not re.search(r"[0-9]", password):
#         return False, _("Password must contain at least one digit.")
#     if not re.search(r"[@$!%*?&]", password):
#         return False, _("Password must contain at least one special character (@, $, !, %, *, ?, &).")
#     return True, None


# class ResUsers(models.Model):
#     _inherit = "res.users"

    

#     @classmethod
#     def _login(cls, db, credential, user_agent_env):
#         # print(credential)
#         if not credential['password']:
#             raise AccessDenied()
#         ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'

#         try:
#             with cls.pool.cursor() as cr:
#                 self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
#                 with self._assert_can_auth():
#                     user = self.search(self._get_login_domain(credential['login']), order=self._get_login_order(),
#                                        limit=1)
#                     if not user:
#                         raise AccessDenied()
#                     user = user.with_user(user)
#                     self.env.cr.execute(
#                         "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
#                         [user.id]
#                     )
#                     hashed = self.env.cr.fetchone()[0]
#                     if not credential['password'] == hashed + 'mobile_otp_login':
#                         user._check_credentials(credential, user_agent_env)

#                     tz = request.httprequest.cookies.get('tz') if request else None
#                     if tz in pytz.all_timezones and (not user.tz or not user.login_date):
#                         # first login or missing tz -> set tz to browser tz
#                         user.tz = tz
#                     user._update_last_login()

#         except AccessDenied:
#             # _logger.info("Login failed for db:%s login:%s from %s", db, credential['login'], ip)
#             raise

#         # _logger.info("Login successful for db:%s login:%s from %s", db, credential['login'], ip)
#         # res = {'uid': user.id}
#         return {'uid': user.id}




#     @api.model
#     def _check_password(self, password):
#         """
#         Override Odoo's password check to enforce strong passwords everywhere.
#         """
#         valid, message = _check_password_strength(password)
#         if not valid:
#             _logger.warning("Weak password attempt for user ID %s: %s", self.id, message)
#             raise ValidationError(message)

#         return super(ResUsers, self)._check_password(password)


#     def change_password(self, old_password, new_password):
#         """
#         Override password change to enforce rules.
#         Works with portal (2 args) and admin flows.
#         """
#         # Odoo portal usually provides `new_password` twice (new1/new2).
#         # If confirm password is in request.params, validate it.
#         confirm_password = request.params.get("confirm_password") or request.params.get("new_password2")
#         if confirm_password and new_password != confirm_password:
#             raise ValidationError(_("The new password and its confirmation do not match."))

#         valid, message = _check_password_strength(new_password)
#         if not valid:
#             raise ValidationError(message)

#         return super(ResUsers, self).change_password(old_password, new_password)

        
 