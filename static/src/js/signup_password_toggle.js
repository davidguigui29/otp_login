/** @odoo-module */

import { whenReady } from "@odoo/owl";

whenReady(() => {
    const checkbox = document.querySelector(".show-password-checkbox");
    if (checkbox) {
        const passwordFields = document.querySelectorAll("#password, #confirm_password");

        // Function to apply toggle
        const applyToggle = () => {
            passwordFields.forEach((input) => {
                input.type = checkbox.checked ? "text" : "password";
            });
        };

        // Run on page load
        applyToggle();

        // Run on checkbox change
        checkbox.addEventListener("change", applyToggle);
    }
});

