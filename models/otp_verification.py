from odoo import fields, models, api
from datetime import datetime, timedelta

class OtpVerification(models.Model):
    _name = "otp.verification"
    _description = 'Otp Verification'

    otp = fields.Text(string="OTP")
    state = fields.Selection([
            ('verified', 'Verified'),
            ('unverified', 'Unverified'),
            ('rejected', 'Rejected')], string="State", default="unverified")
    email = fields.Char(string="email")

    sent_at = fields.Datetime(string="Sent At", default=fields.Datetime.now)

    @api.model
    def _cron_delete_verified_otp(self):
        otp = self.search([('state', '=', 'verified')])
        otp.unlink()

