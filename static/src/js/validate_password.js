/** @odoo-module */

import { whenReady } from "@odoo/owl";

whenReady(() => {
    const passwordField = document.querySelector("#password");
    const confirmField = document.querySelector("#confirm_password");
    const form = document.querySelector("form");
    
    if (!passwordField || !confirmField || !form) return;

    // Create feedback container
    const feedback = document.createElement("div");
    feedback.classList.add("password-feedback");
    feedback.style.color = "red";
    feedback.style.marginTop = "5px";
    passwordField.insertAdjacentElement("afterend", feedback);

    function validatePassword() {
        const password = passwordField.value;
        const confirm = confirmField.value;
        let errors = [];

        if (password.length < 8) {
            errors.push("At least 8 characters");
        }
        if (!/[A-Z]/.test(password)) {
            errors.push("At least one uppercase letter");
        }
        if (!/[a-z]/.test(password)) {
            errors.push("At least one lowercase letter");
        }
        if (!/[0-9]/.test(password)) {
            errors.push("At least one number");
        }
        if (!/[^A-Za-z0-9]/.test(password)) {
            errors.push("At least one special character");
        }
        if (confirm && password !== confirm) {
            errors.push("Passwords do not match");
        }

        if (errors.length > 0) {
            feedback.innerHTML = "❌ " + errors.join("<br>❌ ");
            feedback.style.color = "red";
            return false;
        } else {
            feedback.textContent = "✅ Strong password";
            feedback.style.color = "green";
            return true;
        }
    }

    // Live validation
    passwordField.addEventListener("input", validatePassword);
    confirmField.addEventListener("input", validatePassword);

    // Prevent weak submission
    form.addEventListener("submit", (e) => {
        if (!validatePassword()) {
            e.preventDefault();
            alert("Please use a strong password before submitting.");
        }
    });
});
