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
})();
