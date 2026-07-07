document.addEventListener('DOMContentLoaded', () => {
    // 1. Theme Management
    const themeToggle = document.getElementById('theme-toggle');
    const themeMenu = document.getElementById('theme-menu');
    const themeButtons = document.querySelectorAll('[data-set-theme]');
    const html = document.documentElement;

    // Load saved theme or default to system
    const savedTheme = localStorage.getItem('fluxmedia-theme') || 'system';
    setTheme(savedTheme);

    // Toggle menu
    themeToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        themeMenu.classList.toggle('show');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!themeToggle.contains(e.target) && !themeMenu.contains(e.target)) {
            themeMenu.classList.remove('show');
        }
    });

    // Theme selection
    themeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const theme = btn.getAttribute('data-set-theme');
            setTheme(theme);
            themeMenu.classList.remove('show');
        });
    });

    function setTheme(theme) {
        html.setAttribute('data-theme', theme);
        localStorage.setItem('fluxmedia-theme', theme);
        
        // Update active state in menu
        themeButtons.forEach(btn => {
            if (btn.getAttribute('data-set-theme') === theme) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    // 2. Scroll Reveal Animations
    const revealElements = document.querySelectorAll('.reveal');
    
    const revealOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const revealOnScroll = new IntersectionObserver(function(entries, observer) {
        entries.forEach(entry => {
            if (!entry.isIntersecting) {
                return;
            } else {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        });
    }, revealOptions);

    revealElements.forEach(el => {
        revealOnScroll.observe(el);
    });

    // 3. Copy Commands (Supports multiple buttons)
    const copyBtns = document.querySelectorAll('.copy-btn');
    copyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const codeBlock = btn.closest('.code-block');
            if (!codeBlock) return;
            
            let textToCopy = '';
            
            // Look for code-inner (used in install box) or code-cmd (used in troubleshooting)
            const codeInner = codeBlock.querySelector('.code-inner');
            if (codeInner) {
                textToCopy = codeInner.textContent.trim().replace(/\s+/g, ' '); // Clean up newlines if any
            } else {
                const codeCmd = codeBlock.querySelector('.code-cmd');
                if (codeCmd) textToCopy = codeCmd.textContent.trim();
            }

            if (textToCopy) {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const originalHTML = btn.innerHTML;
                    btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
                    setTimeout(() => {
                        btn.innerHTML = originalHTML;
                    }, 2000);
                });
            }
        });
    });

    // 4. Draggable Terminal
    const terminal = document.querySelector('.terminal-mockup');
    const handle = document.querySelector('.terminal-header');
    
    if (terminal && handle) {
        let isDragging = false;
        let startX, startY;
        let currentX = 0;
        let currentY = 0;

        handle.addEventListener('mousedown', (e) => {
            isDragging = true;
            terminal.style.transition = 'none';
            startX = e.clientX - currentX;
            startY = e.clientY - currentY;
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            currentX = e.clientX - startX;
            currentY = e.clientY - startY;
            
            const boundsX = window.innerWidth / 2;
            const boundsY = window.innerHeight / 2;
            currentX = Math.max(-boundsX, Math.min(boundsX, currentX));
            currentY = Math.max(-boundsY, Math.min(boundsY, currentY));
            
            terminal.style.transform = `translate(${currentX}px, ${currentY}px) rotateX(0deg)`;
        });

        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                terminal.style.transition = 'transform 0.5s ease';
            }
        });
    }

    // 5. Flip Cards
    const flipCards = document.querySelectorAll('.flip-card');
    flipCards.forEach(card => {
        card.addEventListener('click', () => {
            card.classList.toggle('is-flipped');
        });
    });

    // 6. Magnetic Buttons
    const magnets = document.querySelectorAll('.btn');
    
    magnets.forEach(magnet => {
        magnet.addEventListener('mousemove', (e) => {
            const position = magnet.getBoundingClientRect();
            const x = e.clientX - position.left - position.width / 2;
            const y = e.clientY - position.top - position.height / 2;
            
            magnet.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px)`;
        });
        
        magnet.addEventListener('mouseout', (e) => {
            magnet.style.transform = `translate(0px, 0px)`;
        });
    });

    // 7. Global Mouse Follower
    const follower = document.createElement('div');
    follower.className = 'mouse-follower';
    document.body.appendChild(follower);

    document.addEventListener('mousemove', (e) => {
        follower.style.left = e.clientX + 'px';
        follower.style.top = e.clientY + 'px';
        
        // Only show if mouse moves to avoid weird initial corner state
        if (follower.style.width === "0px" || follower.style.width === "") {
            follower.style.width = "400px";
            follower.style.height = "400px";
        }
    });
    
    const interactables = document.querySelectorAll('a, button, .feature-card-wrapper, .bento-card, .terminal-mockup');
    interactables.forEach(el => {
        el.addEventListener('mouseenter', () => follower.classList.add('active'));
        el.addEventListener('mouseleave', () => follower.classList.remove('active'));
    });

    // 8. Interactive Text Splitting
    const heroTitle = document.querySelector('.hero-highlight');
    if (heroTitle) {
        const text = heroTitle.textContent;
        heroTitle.textContent = '';
        text.split('').forEach(char => {
            const span = document.createElement('span');
            span.textContent = char;
            span.className = char === ' ' ? 'char space' : 'char';
            if (char === ' ') span.style.width = '0.5em';
            heroTitle.appendChild(span);
        });
    }



    // 10. Accordion for Troubleshooting
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const item = header.parentElement;
            const content = item.querySelector('.accordion-content');
            
            // Close other items
            document.querySelectorAll('.accordion-item.active').forEach(activeItem => {
                if (activeItem !== item) {
                    activeItem.classList.remove('active');
                    activeItem.querySelector('.accordion-content').style.maxHeight = 0;
                }
            });

            item.classList.toggle('active');
            if (item.classList.contains('active')) {
                content.style.maxHeight = content.scrollHeight + 'px';
            } else {
                content.style.maxHeight = 0;
            }
        });
    });
});
