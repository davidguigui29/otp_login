# -*- coding: utf-8 -*-
import logging
import string
from random import choice

from odoo import http, _
from odoo.addons.web.controllers.home import Home, ensure_db
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.otp_login.utils.email_templates import otp_login_html

_logger = logging.getLogger(__name__)


class OtpLoginHome(Home):

    # -------------------------------------------------------------------------
    # EMAIL TEMPLATE BUILDERS
    # -------------------------------------------------------------------------
    def _build_login_otp_email(self, email, name, otp_code):
        """Return subject, sender, and HTML body for Login OTP email."""
        company = request.env.company
        company_name = company.name or "Your Company"
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        email_from = company.email or f"noreply@{base_url.split('//')[-1]}"
        company_logo = (
            f"{base_url}/web/image/res.company/{company.id}/logo"
            if company.logo else ""
        )
        company_website = company.website or "#"
        company_phone = company.phone or "N/A"

        subject = f"[{company_name}] Login Verification Code"

        body_html = otp_login_html(company_logo=company_logo, company_name=company_name, name=name, otp_code=otp_code, company_phone=company_phone, company_website=company_website, view_look="neogreen")
        return subject, email_from, body_html

    def _send_login_otp_email(self, email, name, otp_code):
        """Build and send OTP email."""
        subject, email_from, body_html = self._build_login_otp_email(email, name, otp_code)
        mail = request.env["mail.mail"].sudo().create({
            "subject": subject,
            "email_from": email_from,
            "email_to": email,
            "body_html": body_html,
        })
        mail.send()
        _logger.info("OTP email sent to %s", email)
        return True

    # -------------------------------------------------------------------------
    # LOGIN PAGE HANDLER
    # -------------------------------------------------------------------------
    @http.route(website=True)
    def web_login(self, redirect=None, **kw):
        """
        Override default login:
        - Handles OTP flow pages
        - Redirects to Odoo's standard login for password logins
        """
        ensure_db()
        qcontext = dict(request.params)

        # Render custom OTP screens
        if request.httprequest.method == "GET":
            if kw.get("otp_login") and kw.get("otp"):
                return request.render("otp_login.custom_login_template", {"otp": True, "otp_login": True})
            elif kw.get("otp_login"):
                return request.render("otp_login.custom_login_template", {"otp_login": True})
            else:
                return super().web_login(redirect, **kw)

        # POST (form submission)
        if kw.get("login"):
            request.params["login"] = kw["login"].strip()
        if kw.get("password"):
            request.params["password"] = kw["password"].strip()

        return super().web_login(redirect, **kw)

    # -------------------------------------------------------------------------
    # OTP GENERATION
    # -------------------------------------------------------------------------
    def generate_otp(self, length=4):
        return ''.join(choice(string.digits) for _ in range(length))

    # -------------------------------------------------------------------------
    # SEND OTP
    # -------------------------------------------------------------------------
    @http.route("/web/otp/login", type="http", auth="public", website=True, csrf=False)
    def web_otp_login(self, **kw):
        email = str(kw.get("login", "")).strip()
        if not email:
            return request.render("otp_login.custom_login_template", {"error": _("Email is required.")})

        user = request.env["res.users"].sudo().search([("login", "=", email)], limit=1)
        if not user:
            return request.render("otp_login.custom_login_template", {
                "otp": False, "otp_login": True, "login_error": True, "login": email
            })

        otp = self.generate_otp(4)
        self._send_login_otp_email(email, user.name, otp)
        request.env["otp.verification"].sudo().create({"otp": otp, "email": email})

        return request.render("otp_login.custom_login_template", {
            "otp_login": True,
            "otp": True,
            "login": email
        })

    # -------------------------------------------------------------------------
    # VERIFY OTP
    # -------------------------------------------------------------------------
    @http.route("/web/otp/verify", type="http", auth="public", website=True, csrf=False)
    def web_otp_verify(self, **kw):
        email = str(kw.get("login", "")).strip()
        otp_input = str(kw.get("otp", "")).strip()
        if not email or not otp_input:
            return request.render("otp_login.custom_login_template", {
                "otp": True, "otp_login": True, "login": email, "otp_error": True
            })

        record = request.env["otp.verification"].sudo().search(
            [("email", "=", email)], order="create_date desc", limit=1
        )
        if not record:
            return request.render("otp_login.custom_login_template", {
                "otp": True, "otp_login": True, "login": email, "otp_error": True
            })

        if record.otp != otp_input:
            record.state = "rejected"
            return request.render("otp_login.custom_login_template", {
                "otp": True, "otp_login": True, "login": email, "otp_error": True
            })

        record.state = "verified"
        user = request.env["res.users"].sudo().search([("login", "=", email)], limit=1)
        if not user:
            return request.render("otp_login.custom_login_template", {
                "otp": True, "otp_login": True, "login": email, "otp_error": True
            })

        # Simulate login using special password suffix
        request.env.cr.execute(
            "SELECT COALESCE(password, '') FROM res_users WHERE id=%s", [user.id]
        )
        hashed = request.env.cr.fetchone()[0]
        request.params.update({
            "login": user.login,
            "password": hashed + "mobile_otp_login",
        })
        return self.web_login()

    # -------------------------------------------------------------------------
    # RESEND OTP
    # -------------------------------------------------------------------------
    @http.route("/web/otp/resend", type="json", auth="public", website=True, csrf=False)
    def web_otp_resend(self, **kw):
        data = request.get_json_data() or {}
        email = data.get("login")
        if not email:
            return {"status": "error", "message": "Missing email"}

        user = request.env["res.users"].sudo().search([("login", "=", email)], limit=1)
        if not user:
            return {"status": "error", "message": "Email not found"}

        otp = self.generate_otp(4)
        request.env["otp.verification"].sudo().create({"otp": otp, "email": email})
        self._send_login_otp_email(email, user.name, otp)

        return {"status": "success", "message": "OTP resent successfully"}



