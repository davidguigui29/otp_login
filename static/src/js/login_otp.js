/** @odoo-module **/

import { whenReady } from "@odoo/owl";

whenReady(() => {
    // When user clicks "Login with OTP"
    const otpLink = document.querySelector("a[href*='?otp_login=true']");
    if (otpLink) {
        otpLink.addEventListener("click", function (event) {
            const emailInput = document.querySelector("input[name='login']");
            if (emailInput && emailInput.value) {
                event.preventDefault(); // stop default navigation
                const url = new URL(otpLink.href, window.location.origin);
                url.searchParams.set("email", emailInput.value);
                window.location.href = url.toString();
            }
        });
    }

    // On OTP page: auto-fill email input
    const params = new URLSearchParams(window.location.search);
    if (params.has("otp_login") && params.has("email")) {
        const otpEmailInput = document.querySelector("#login");
        if (otpEmailInput) {
            otpEmailInput.value = params.get("email");
        }
    }


        // Resend OTP handler
    const resendBtn = document.querySelector("#resend_otp_btn");
    if (resendBtn) {
        resendBtn.addEventListener("click", async function () {
            // const emailInput = document.querySelector("#login");
            const emailInput = document.querySelector("#otp_login_hidden") || document.querySelector("input[name='login']");
            console.log(emailInput.value)
            if (!emailInput || !emailInput.value) {
                alert("Email missing, please go back and try again.");
                return;
            }

            try {
                const response = await fetch("/web/otp/resend", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ login: emailInput.value }),
                });

                const raw = await response.json();
                const data = raw.result || raw;

                if (data.status === "success") {
                    startCountdown(30);
                } else {
                    alert(data.message || "Failed to resend OTP");
                }
            } catch (err) {
                console.error("Error resending OTP:", err);
                alert("Something went wrong. Try again.");
            }
        });
    }

    function startCountdown(seconds) {
        let countdown = seconds;
        const span = document.querySelector("#countdown");
        const resendBtn = document.querySelector("#resend_otp_btn");

        resendBtn.disabled = true;
        span.textContent = countdown;

        const interval = setInterval(() => {
            countdown--;
            span.textContent = countdown;
            if (countdown <= 0) {
                clearInterval(interval);
                resendBtn.disabled = false;
                span.textContent = "30";
            }
        }, 1000);
    }

        // Auto-start countdown when OTP form is shown
    const otpForm = document.querySelector("#form_otp");
    if (otpForm) {
        startCountdown(30);
    }

});

