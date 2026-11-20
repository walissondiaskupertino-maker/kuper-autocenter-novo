(function () {
    const body = document.body;
    const sidebarToggle = document.querySelector(".sidebar-toggle");
    const sidebarClose = document.querySelector(".sidebar-close");
    const backdrop = document.querySelector(".sidebar-backdrop");

    function setSidebar(open) {
        body.classList.toggle("sidebar-open", open);
        if (sidebarToggle) {
            sidebarToggle.setAttribute("aria-expanded", String(open));
        }
    }

    sidebarToggle?.addEventListener("click", () => setSidebar(true));
    sidebarClose?.addEventListener("click", () => setSidebar(false));
    backdrop?.addEventListener("click", () => setSidebar(false));

    document.querySelectorAll("[data-confirm]").forEach((element) => {
        element.addEventListener("click", (event) => {
            if (!window.confirm(element.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setSidebar(false);
        }
    });

    function formatDocument(value, cpfOnly) {
        const digits = value.replace(/\D/g, "").slice(0, cpfOnly ? 11 : 14);
        if (digits.length <= 11 || cpfOnly) {
            return digits
                .replace(/^(\d{3})(\d)/, "$1.$2")
                .replace(/^(\d{3}\.\d{3})(\d)/, "$1.$2")
                .replace(/^(\d{3}\.\d{3}\.\d{3})(\d{1,2})$/, "$1-$2");
        }
        return digits
            .replace(/^(\d{2})(\d)/, "$1.$2")
            .replace(/^(\d{2}\.\d{3})(\d)/, "$1.$2")
            .replace(/^(\d{2}\.\d{3}\.\d{3})(\d)/, "$1/$2")
            .replace(/^(\d{2}\.\d{3}\.\d{3}\/\d{4})(\d{1,2})$/, "$1-$2");
    }

    function formatPhone(value) {
        let digits = value.replace(/\D/g, "").slice(0, 13);
        let country = "";
        if (digits.startsWith("55") && digits.length > 11) {
            country = "+55 ";
            digits = digits.slice(2);
        }
        if (digits.length <= 2) {
            return country + (digits ? `(${digits}` : "");
        }
        const area = digits.slice(0, 2);
        const number = digits.slice(2, 11);
        const prefix = `${country}(${area}) `;
        if (number.length <= 4) {
            return prefix + number;
        }
        const split = number.length > 8 ? 5 : 4;
        return `${prefix}${number.slice(0, split)}-${number.slice(split)}`;
    }

    document.querySelectorAll("[data-mask]").forEach((input) => {
        const applyMask = () => {
            if (input.dataset.mask === "document") {
                input.value = formatDocument(input.value, false);
            } else if (input.dataset.mask === "cpf") {
                input.value = formatDocument(input.value, true);
            } else if (input.dataset.mask === "phone") {
                input.value = formatPhone(input.value);
            } else if (input.dataset.mask === "plate") {
                input.value = input.value.toUpperCase().replace(/[^A-Z0-9-]/g, "").slice(0, 8);
            }
        };
        input.addEventListener("input", applyMask);
        applyMask();
    });

    document.querySelectorAll("[data-uppercase]").forEach((input) => {
        input.addEventListener("input", () => {
            input.value = input.value.toUpperCase();
        });
    });

    document.querySelectorAll("[data-decimal]").forEach((input) => {
        input.form?.addEventListener("submit", () => {
            const value = input.value.trim();
            if (value.includes(",")) {
                input.value = value.replace(/\./g, "").replace(",", ".");
            }
        });
    });

    document.querySelectorAll("[data-filter-select]").forEach((input) => {
        const select = document.getElementById(input.dataset.filterSelect);
        if (!select) {
            return;
        }
        input.addEventListener("input", () => {
            const query = input.value.trim().toLocaleLowerCase();
            Array.from(select.options).forEach((option) => {
                option.hidden = Boolean(option.value) && !option.text.toLocaleLowerCase().includes(query);
            });
            if (select.selectedOptions[0]?.hidden) {
                select.value = "";
            }
        });
        input.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
            }
        });
    });
})();
