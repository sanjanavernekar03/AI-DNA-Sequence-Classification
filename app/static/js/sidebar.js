/**
 * DNAura — Global Professional Sidebar Controller
 * Single global sidebar state persisted in localStorage.
 */

(function () {
    const STORAGE_KEY = "genomix_sidebar_state";
    const BREAKPOINT = 992; // px

    function getStoredState() {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored === "open" || stored === "closed") {
                return stored;
            }
        } catch (e) {}
        // Default: open on desktop, closed on mobile
        return window.innerWidth >= BREAKPOINT ? "open" : "closed";
    }

    function isMobile() {
        return window.innerWidth < BREAKPOINT;
    }

    function applySidebarState(state, animate = true) {
        const root = document.documentElement;
        const body = document.body;
        const sidebar = document.querySelector(".app-sidebar");
        const backdrop = getOrCreateBackdrop();

        if (!animate) {
            root.classList.add("no-sidebar-transition");
        } else {
            root.classList.remove("no-sidebar-transition");
        }

        if (isMobile()) {
            // Mobile Overlay Drawer Logic
            root.classList.remove("sidebar-collapsed");
            if (state === "open") {
                if (sidebar) sidebar.classList.add("show");
                backdrop.classList.add("show");
                body.style.overflow = "hidden";
            } else {
                if (sidebar) sidebar.classList.remove("show");
                backdrop.classList.remove("show");
                body.style.overflow = "";
            }
        } else {
            // Desktop Collapse Logic
            if (sidebar) sidebar.classList.remove("show");
            backdrop.classList.remove("show");
            body.style.overflow = "";

            if (state === "closed") {
                root.classList.add("sidebar-collapsed");
                body.classList.add("sidebar-collapsed");
            } else {
                root.classList.remove("sidebar-collapsed");
                body.classList.remove("sidebar-collapsed");
            }
        }

        // Save preference
        try {
            localStorage.setItem(STORAGE_KEY, state);
        } catch (e) {}

        // Update toggle button icon/active state if present
        updateToggleButtonUI(state);

        // Notify charts and responsive layouts to recalculate after transition
        setTimeout(() => {
            window.dispatchEvent(new Event("resize"));
            if (!animate) {
                root.classList.remove("no-sidebar-transition");
            }
        }, 300);
    }

    function getOrCreateBackdrop() {
        let backdrop = document.querySelector(".sidebar-backdrop");
        if (!backdrop) {
            backdrop = document.createElement("div");
            backdrop.className = "sidebar-backdrop";
            document.body.appendChild(backdrop);

            backdrop.addEventListener("click", () => {
                applySidebarState("closed", true);
            });
        }
        return backdrop;
    }

    function updateToggleButtonUI(state) {
        document.querySelectorAll(".sidebar-toggle-btn").forEach(btn => {
            if (state === "closed") {
                btn.classList.add("active");
                btn.setAttribute("title", "Open Sidebar");
                btn.setAttribute("aria-expanded", "false");
            } else {
                btn.classList.remove("active");
                btn.setAttribute("title", "Close Sidebar");
                btn.setAttribute("aria-expanded", "true");
            }
        });
    }

    function toggleSidebar() {
        const currentState = document.documentElement.classList.contains("sidebar-collapsed") || 
                             (isMobile() && !document.querySelector(".app-sidebar")?.classList.contains("show"))
                             ? "closed" 
                             : "open";

        const nextState = currentState === "open" ? "closed" : "open";
        applySidebarState(nextState, true);
    }

    // Apply state as early as possible before DOM ready to reduce layout shift
    const initialState = getStoredState();
    if (initialState === "closed" && !isMobile()) {
        document.documentElement.classList.add("sidebar-collapsed");
    }

    document.addEventListener("DOMContentLoaded", () => {
        applySidebarState(initialState, false);

        // Global delegated event listener for sidebar toggle buttons
        document.body.addEventListener("click", (e) => {
            const toggleBtn = e.target.closest(".sidebar-toggle-btn");
            if (toggleBtn) {
                e.preventDefault();
                toggleSidebar();
            }
        });

        // Close mobile drawer on ESC key
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && isMobile()) {
                const sidebar = document.querySelector(".app-sidebar");
                if (sidebar && sidebar.classList.contains("show")) {
                    applySidebarState("closed", true);
                }
            }
        });

        // Handle window resize between desktop and mobile
        let resizeTimer;
        window.addEventListener("resize", () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                const state = getStoredState();
                applySidebarState(state, false);
            }, 150);
        });
    });

    // Expose Global Manager API
    window.SidebarManager = {
        toggle: toggleSidebar,
        open: () => applySidebarState("open", true),
        close: () => applySidebarState("closed", true),
        getState: getStoredState
    };
})();
