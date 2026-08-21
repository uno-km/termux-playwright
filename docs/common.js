/**
 * AMEVA Ecosystem - Unified Common Client Script (shared/common.js)
 * High-Clarity Enterprise Open-Source Standard
 * 
 * Features:
 * 1. Universal Hamburger Menu Toggle (Desktop Collapse & Mobile Drawer)
 * 2. Sidebar Section Accordions (Collapsible/Expandable Categories)
 * 3. Automatic Code Block Copy Tooltips
 * 4. Sidebar Active Link Highlighting
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── 1. Setup Universal Hamburger Menu Toggle ─────────────────────────────
    const header = document.querySelector('header');
    const container = document.querySelector('.container');
    const sidebar = document.querySelector('.sidebar');

    if (header && sidebar) {
        // Find or create Hamburger Toggle Button
        let toggleBtn = header.querySelector('.menu-toggle-btn');
        if (!toggleBtn) {
            toggleBtn = document.createElement('button');
            toggleBtn.className = 'menu-toggle-btn';
            toggleBtn.setAttribute('aria-label', 'Toggle Navigation Menu');
            toggleBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
                <span class="menu-toggle-label">Menu</span>
            `;
            
            // Insert at beginning of header-controls or right after header-brand
            const controls = header.querySelector('.header-controls');
            if (controls) {
                controls.insertBefore(toggleBtn, controls.firstChild);
            } else {
                header.appendChild(toggleBtn);
            }
        }

        // Toggle action
        toggleBtn.addEventListener('click', () => {
            const isMobile = window.innerWidth <= 960;
            if (isMobile) {
                sidebar.classList.toggle('mobile-open');
                toggleBtn.classList.toggle('active');
            } else {
                sidebar.classList.toggle('collapsed');
                if (container) container.classList.toggle('sidebar-collapsed');
                toggleBtn.classList.toggle('active');
            }
        });

        // Close mobile menu on link click
        sidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 960) {
                    sidebar.classList.remove('mobile-open');
                    toggleBtn.classList.remove('active');
                }
            });
        });
    }

    // ── 2. Setup Collapsible Sidebar Section Accordions ───────────────────────
    if (sidebar) {
        const headers = sidebar.querySelectorAll('h3');
        headers.forEach(h3 => {
            const ul = h3.nextElementSibling;
            if (!ul || ul.tagName !== 'UL') return;

            h3.classList.add('collapsible-header');

            // Add arrow icon if missing
            if (!h3.querySelector('.accordion-icon')) {
                const icon = document.createElement('span');
                icon.className = 'accordion-icon';
                icon.textContent = '▾';
                h3.appendChild(icon);
            }

            // Check if this category has an active link
            const hasActiveLink = ul.querySelector('a.active') !== null;
            
            // If on mobile, collapse secondary categories by default, keep active open
            if (window.innerWidth <= 768 && !hasActiveLink && h3.textContent.includes('Ecosystem')) {
                ul.classList.add('collapsed');
                h3.classList.add('collapsed');
                h3.querySelector('.accordion-icon').textContent = '▸';
            }

            // Click listener for section toggle
            h3.addEventListener('click', () => {
                const isCollapsed = ul.classList.toggle('collapsed');
                h3.classList.toggle('collapsed', isCollapsed);
                const icon = h3.querySelector('.accordion-icon');
                if (icon) {
                    icon.textContent = isCollapsed ? '▸' : '▾';
                }
            });
        });
    }

    // ── 3. Setup Copy Buttons on all <pre><code> blocks ───────────────────────
    document.querySelectorAll('pre').forEach((pre) => {
        if (pre.querySelector('.copy-code-btn')) return;

        const btn = document.createElement('button');
        btn.className = 'copy-code-btn';
        btn.setAttribute('aria-label', 'Copy code');
        btn.textContent = 'Copy';

        btn.addEventListener('click', async () => {
            const codeBlock = pre.querySelector('code') || pre;
            const textToCopy = codeBlock.innerText.trim();
            try {
                await navigator.clipboard.writeText(textToCopy);
                btn.textContent = 'Copied!';
                btn.style.backgroundColor = '#16a34a';
                btn.style.color = '#ffffff';

                setTimeout(() => {
                    btn.textContent = 'Copy';
                    btn.style.backgroundColor = '';
                    btn.style.color = '';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy: ', err);
            }
        });

        pre.appendChild(btn);
    });

    // ── 4. Auto-highlight Active Link in Sidebar ───────────────────────────────
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar a').forEach(link => {
        const href = link.getAttribute('href');
        if (!href) return;
        
        // Exact match or subpage match
        if (href === currentPath || currentPath.endsWith(href) || (href === './' && currentPath.endsWith('/'))) {
            link.classList.add('active');
            // Ensure parent ul and category are open
            const parentUl = link.closest('ul');
            if (parentUl) {
                parentUl.classList.remove('collapsed');
                const prevH3 = parentUl.previousElementSibling;
                if (prevH3 && prevH3.tagName === 'H3') {
                    prevH3.classList.remove('collapsed');
                    const icon = prevH3.querySelector('.accordion-icon');
                    if (icon) icon.textContent = '▾';
                }
            }
        }
    });
});
