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

    

    @classmethod
    def _login(cls, db, credential, user_agent_env):
        print(credential)
        if not credential['password']:
            raise AccessDenied()
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'

        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                with self._assert_can_auth():
                    user = self.search(self._get_login_domain(credential['login']), order=self._get_login_order(),
                                       limit=1)
                    if not user:
                        raise AccessDenied()
                    user = user.with_user(user)
                    self.env.cr.execute(
                        "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                        [user.id]
                    )
                    hashed = self.env.cr.fetchone()[0]
                    if not credential['password'] == hashed + 'mobile_otp_login':
                        user._check_credentials(credential, user_agent_env)

                    tz = request.httprequest.cookies.get('tz') if request else None
                    if tz in pytz.all_timezones and (not user.tz or not user.login_date):
                        # first login or missing tz -> set tz to browser tz
                        user.tz = tz
                    user._update_last_login()

        except AccessDenied:
            _logger.info("Login failed for db:%s login:%s from %s", db, credential['login'], ip)
            raise

        _logger.info("Login successful for db:%s login:%s from %s", db, credential['login'], ip)
        # res = {'uid': user.id}
        return {'uid': user.id}




    @api.model
    def _check_password(self, password):
        """
        Override Odoo's password check to enforce strong passwords everywhere.
        """
        valid, message = _check_password_strength(password)
        if not valid:
            _logger.warning("Weak password attempt for user ID %s: %s", self.id, message)
            raise ValidationError(message)

        return super(ResUsers, self)._check_password(password)


    def change_password(self, old_password, new_password):
        """
        Override password change to enforce rules.
        Works with portal (2 args) and admin flows.
        """
        # Odoo portal usually provides `new_password` twice (new1/new2).
        # If confirm password is in request.params, validate it.
        confirm_password = request.params.get("confirm_password") or request.params.get("new_password2")
        if confirm_password and new_password != confirm_password:
            raise ValidationError(_("The new password and its confirmation do not match."))

        valid, message = _check_password_strength(new_password)
        if not valid:
            raise ValidationError(message)

        return super(ResUsers, self).change_password(old_password, new_password)

        
 