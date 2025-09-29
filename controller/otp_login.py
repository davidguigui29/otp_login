import logging
from random import choice
import string

from odoo.addons.web.controllers.home import Home, ensure_db
from odoo import http, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
_logger = logging.getLogger(__name__)


class OtpLoginHome(Home):

    def _build_login_otp_email(self, email, name, otp_code):
        """Return subject, body_html for Login OTP email."""
        company = request.env.company
        email_from = company.email or "noreply@example.com"
        company_name = company.name or "Your Company"
        company_logo = ""
        if company.logo:
            base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
            company_logo = f"{base_url}/web/image/res.company/{company.id}/logo"
        company_website = company.website or "#"
        company_phone = company.phone or "N/A"

        subject = _(f"[{company_name}] Verify Your Login - OTP Required")
        # {"<img src='%s' alt='%s' height='50' style='margin-bottom:10px;'>" % (company_logo, company_name) if company_logo else ""}



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
                            To complete your login to <b>{company_name}</b>, please confirm your identity using the OTP below.
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
                            If you did not request to log in, kindly ignore this email.
                        </p>

                        <p style="margin-top:30px;">Best regards,<br><b>{company_name} Security Team</b></p>
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

    def _send_login_otp_email(self, email, name, otp_code):
        """Build and send OTP email for login verification."""
        subject, email_from, body_html = self._build_login_otp_email(email, name, otp_code)
        mail = request.env['mail.mail'].sudo().create({
            'subject': subject,
            'email_from': email_from,
            'email_to': email,
            'body_html': body_html,
        })
        mail.send()
        return mail

    
    @http.route(website=True)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        qcontext = request.params.copy()

        if request.httprequest.method == 'GET':

            if "otp_login" and "otp" in kw:
                if kw["otp_login"] and kw["otp"]:
                    return request.render("otp_login.custom_login_template", {'otp': True, 'otp_login': True})
            if "otp_login" in kw: #checks if the keyword "otp_login" exists in the dict "kw".
                if kw["otp_login"]: #checks if the value of "otp_login" is true.
                    return request.render("otp_login.custom_login_template", {'otp_login': True})
            else:
                return super(OtpLoginHome, self).web_login(redirect, **kw)
        else:
            if kw.get('login'):
                request.params['login'] = kw.get('login').strip()
            if kw.get('password'):
                request.params['password'] = kw.get('password').strip()
            return super(OtpLoginHome, self).web_login(redirect, **kw)

        return request.render("otp_login.custom_login_template", {})



    @http.route('/web/otp/login', type='http', auth='public', website=True, csrf=False)
    def web_otp_login(self, **kw):
        qcontext = request.params.copy()
        email = str(qcontext.get('login'))
        user_id = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)

        if user_id:
            OTP = self.generate_otp(4)
            _logger.info(f"Generated OTP for {email}: {OTP}")

            

            vals = {
                'otp': OTP,
                'email': email
            }
            
            # Send mail
            self._send_login_otp_email(email, user_id.name, OTP)

            # Save OTP in your verification model
            request.env['otp.verification'].sudo().create(vals)


            return request.render("otp_login.custom_login_template", {
                "otp_login": True,
                "otp": True,
                "otp_no": OTP,
                "login": email,   # <-- pass email so hidden field can use it
            })


        else:
            return request.render("otp_login.custom_login_template", {
                'otp': False,
                'otp_login': True,
                'login_error': True,
                'login': email,
            })


    @http.route('/web/otp/verify', type='http', auth='public', website=True, csrf=False)
    def web_otp_verify(self, *args, **kw):
        qcontext = request.params.copy()
        email = str(kw.get('login'))
        res_id = request.env['otp.verification'].search([('email', '=', email)], order="create_date desc", limit=1)

        try:
            otp = str(kw.get('otp'))
            otp_no = res_id.otp
            if otp_no == otp:
                res_id.state = 'verified'
                user_id = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
                request.env.cr.execute(
                    "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                    [user_id.id]
                )
                hashed = request.env.cr.fetchone()[0]
                qcontext.update({'login': user_id.sudo().login,
                                 'name': user_id.sudo().partner_id.name,
                                 'password': hashed + 'mobile_otp_login'})
                request.params.update(qcontext)
                return self.web_login(*args, **kw)
            else:
                res_id.state = 'rejected'
                response = request.render('otp_login.custom_login_template', {'otp': True, 'otp_login': True,
                                                                                   'login': email,
                                                                                   'otp_error': True,})
                return response
        except UserError as e:
            qcontext['error'] = e.name or e.value

        response = request.render('otp_login.custom_login_template', {'otp': True, 'otp_login': True,
                                                                           'login': email})
        return response



    @http.route('/web/otp/resend', type='json', auth='public', website=True, csrf=False)
    def web_otp_resend(self, **kw):
        data = request.get_json_data()
        email = data.get("login")
        _logger.info(f"Resend OTP request for: {email}")
        _logger.info(f"Resend OTP raw kw: {kw}, qcontext: {request.params}, {data}")


        if not email:
            return {"status": "error", "message": "Missing email"}


        user_id = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if not user_id:
            return {"status": "error", "message": "Email not found"}

        # Generate OTP
        OTP = self.generate_otp(4)
        _logger.info(f"Resent OTP for {email}: {OTP}")

        # Save OTP
        request.env['otp.verification'].sudo().create({
            "otp": OTP,
            "email": email
        })

        # Send mail
        self._send_login_otp_email(email, user_id.name, OTP)

        return {"status": "success", "message": "OTP resent successfully"}


    def generate_otp(self, number_of_digits):
        otp = ''.join(choice(string.digits) for _ in range(number_of_digits))
        return otp


