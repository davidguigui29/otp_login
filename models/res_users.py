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

    # -------------------------------------------------------------------------
    # LOGIN OVERRIDE
    # -------------------------------------------------------------------------
    @classmethod
    def _login(cls, db, credential, user_agent_env):
        """
        Custom login handler that supports:
        - Normal login with password
        - Mobile OTP login (password + 'mobile_otp_login' suffix)
        - OAuth login (delegated cleanly)
        """
        ip = request.httprequest.environ.get("REMOTE_ADDR") if request else "n/a"

        # ✅ 1. Detect OAuth login via route or credential
        if (
            request and "/auth_oauth/" in request.httprequest.path
        ) or (
            isinstance(credential, dict) and "oauth_provider_id" in credential
        ):
            _logger.info("Bypassing OTP for OAuth login from %s", ip)
            # Delegate directly to base class (do not enforce password)
            return super(ResUsers, cls)._login(db, credential, user_agent_env)

        # ✅ 2. Continue with normal or OTP-based password login
        if not isinstance(credential, dict) or "password" not in credential or not credential["password"]:
            _logger.warning("Login attempt missing password from %s", ip)
            raise AccessDenied(_("Missing password."))

        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]

                with self._assert_can_auth():
                    user = self.search(self._get_login_domain(credential["login"]),
                                    order=self._get_login_order(), limit=1)
                    if not user:
                        raise AccessDenied(_("User not found."))

                    user = user.with_user(user)

                    cr.execute("SELECT COALESCE(password, '') FROM res_users WHERE id=%s", [user.id])
                    hashed = cr.fetchone()[0]

                    # OTP special case
                    if credential["password"] != hashed + "mobile_otp_login":
                        user._check_credentials(credential, user_agent_env)

                    # Auto timezone update on first login
                    tz = request.httprequest.cookies.get("tz") if request else None
                    if tz in pytz.all_timezones and (not user.tz or not user.login_date):
                        user.tz = tz

                    user._update_last_login()

        except AccessDenied:
            _logger.warning("Login failed for %s from %s", credential.get("login"), ip)
            raise

        _logger.info("Login successful for %s from %s", credential.get("login"), ip)
        return {"uid": user.id}


    # -------------------------------------------------------------------------
    # PASSWORD STRENGTH ENFORCEMENT
    # -------------------------------------------------------------------------
    @api.model
    def _check_password(self, password):
        """Enforce password strength globally."""
        valid, message = _check_password_strength(password)
        if not valid:
            _logger.warning("Weak password attempt for user %s: %s", self.id, message)
            raise ValidationError(message)
        return super(ResUsers, self)._check_password(password)

    def change_password(self, old_password, new_password):
        """Override password change to validate complexity and confirmation."""
        confirm_password = (
            request.params.get("confirm_password") or request.params.get("new_password2")
        )
        if confirm_password and new_password != confirm_password:
            raise ValidationError(_("The new password and its confirmation do not match."))

        valid, message = _check_password_strength(new_password)
        if not valid:
            raise ValidationError(message)

        return super(ResUsers, self).change_password(old_password, new_password)



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

        
 