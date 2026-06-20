document.addEventListener('DOMContentLoaded', () => {
    console.log("Inventario Seguro UI Loaded");

    // Sidebar Toggle
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    const closeBtn = document.getElementById('sidebarClose');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
            // Background overlay logic for mobile
            let overlay = document.getElementById('sidebarOverlay');
            if(!sidebar.classList.contains('-translate-x-full')){
                if(!overlay) {
                    overlay = document.createElement('div');
                    overlay.id = 'sidebarOverlay';
                    overlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden transition-opacity';
                    document.body.appendChild(overlay);
                    
                    overlay.addEventListener('click', () => {
                        sidebar.classList.add('-translate-x-full');
                        overlay.remove();
                    });
                }
            } else if (overlay) {
                overlay.remove();
            }
        });
    }

    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => {
            sidebar.classList.add('-translate-x-full');
            const overlay = document.getElementById('sidebarOverlay');
            if (overlay) overlay.remove();
        });
    }

    // Password Toggle
    const passToggles = document.querySelectorAll('.toggle-password');
    passToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const inputId = this.getAttribute('data-target');
            const input = document.getElementById(inputId);
            
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    this.classList.remove('fa-eye');
                    this.classList.add('fa-eye-slash');
                } else {
                    input.type = 'password';
                    this.classList.remove('fa-eye-slash');
                    this.classList.add('fa-eye');
                }
            }
        });
    });
});
