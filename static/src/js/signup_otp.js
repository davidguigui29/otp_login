/** @odoo-module **/

import { whenReady } from "@odoo/owl";

whenReady(() => {
    const COUNTDOWN_KEY = "signup_otp_countdown_expiry";

    // Resend OTP handler (signup)
    const resendBtn = document.querySelector("#resend_signup_otp_btn");
    if (resendBtn) {
        resendBtn.addEventListener("click", async function () {
            const emailInput = document.querySelector("#signup_email") || document.querySelector("input[name='login']");
            const nameInput = document.querySelector("input[name='name']");
            // console.log(nameInput)

            if (!nameInput || !nameInput.value) {
                alert("Name missing, please go back and try again")
                return;
            }

            if (!emailInput || !emailInput.value) {
                alert("Email missing, please go back and try again.");
                return;
            }

            // 🔒 Check if countdown is still active
            const expiry = parseInt(localStorage.getItem(COUNTDOWN_KEY) || "0", 10);
            if (expiry > Date.now()) {
                alert("Please wait until the countdown finishes before resending.");
                return;
            }

            try {
                const response = await fetch("/web/signup/otp/resend", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ login: emailInput.value, name: nameInput.value }),
                });

                const raw = await response.json();
                const data = raw.result || raw;

                if (data.status === "success") {
                    const newExpiry = Date.now() + 30 * 1000; // 30s
                    localStorage.setItem(COUNTDOWN_KEY, newExpiry);
                    startCountdown();
                } else {
                    alert(data.message || "Failed to resend OTP");
                }
            } catch (err) {
                console.error("Error resending OTP:", err);
                alert("Something went wrong. Try again.");
            }
        });
    }

    function startCountdown() {
        const span = document.querySelector("#signup_countdown");
        const resendBtn = document.querySelector("#resend_signup_otp_btn");

        function updateCountdown() {
            const expiry = parseInt(localStorage.getItem(COUNTDOWN_KEY) || "0", 10);
            const remaining = Math.max(0, Math.floor((expiry - Date.now()) / 1000));

            if (remaining > 0) {
                resendBtn.disabled = true;
                span.textContent = remaining;
                return true; // still running
            } else {
                resendBtn.disabled = false;
                span.textContent = "30";
                localStorage.removeItem(COUNTDOWN_KEY);
                return false; // finished
            }
        }

        // Run immediately, then every second
        if (updateCountdown()) {
            const interval = setInterval(() => {
                if (!updateCountdown()) clearInterval(interval);
            }, 1000);
        }
    }

    // --- First load handler ---
    const otpForm = document.querySelector("#form_signup_otp");
    if (otpForm) {
        const termsCheckbox = otpForm.querySelector("#terms_conditions");
        const submitBtn = otpForm.querySelector("button[type='submit']");

        if (termsCheckbox && submitBtn) {
            // Initial state
            submitBtn.disabled = true;

            termsCheckbox.addEventListener("change", function () {
                submitBtn.disabled = !this.checked;
            });

            // Safety: block form submit if not checked
            otpForm.addEventListener("submit", function (ev) {
                if (!termsCheckbox.checked) {
                    ev.preventDefault();
                    alert("You must agree to the Terms of Service and Privacy Policy.");
                    submitBtn.disabled = true;
                }
            });
        }
        if (!localStorage.getItem(COUNTDOWN_KEY)) {
            const expiry = Date.now() + 30 * 1000;
            localStorage.setItem(COUNTDOWN_KEY, expiry);
        }
        startCountdown();
    }
});




// /** @odoo-module **/

// import { whenReady } from "@odoo/owl";

// whenReady(() => {

//     // Resend OTP handler (signup)
//     const resendBtn = document.querySelector("#resend_signup_otp_btn");
//     if (resendBtn) {
//         resendBtn.addEventListener("click", async function () {
//             const emailInput = document.querySelector("#signup_email") || document.querySelector("input[name='login']");
//             console.log(emailInput)
//             if (!emailInput || !emailInput.value) {
//                 alert("Email missing, please go back and try again.");
//                 return;
//             }

//             try {
//                 const response = await fetch("/web/signup/otp/resend", {
//                     method: "POST",
//                     headers: { "Content-Type": "application/json" },
//                     body: JSON.stringify({ login: emailInput.value }),
//                 });

//                 const raw = await response.json();
//                 const data = raw.result || raw;

//                 if (data.status === "success") {
//                     startCountdown(30);
//                 } else {
//                     alert(data.message || "Failed to resend OTP");
//                 }
//             } catch (err) {
//                 console.error("Error resending OTP:", err);
//                 alert("Something went wrong. Try again.");
//             }
//         });
//     }

//     function startCountdown(seconds) {
//         let countdown = seconds;
//         const span = document.querySelector("#signup_countdown");
//         const resendBtn = document.querySelector("#resend_signup_otp_btn");

//         resendBtn.disabled = true;
//         span.textContent = countdown;

//         const interval = setInterval(() => {
//             countdown--;
//             span.textContent = countdown;
//             if (countdown <= 0) {
//                 clearInterval(interval);
//                 resendBtn.disabled = false;
//                 span.textContent = "30";
//             }
//         }, 1000);
//     }

//     // Auto-start countdown when OTP form is shown (signup)
//     const otpForm = document.querySelector("#form_signup_otp");
//     if (otpForm) {
//         startCountdown(30);
//     }
// });
