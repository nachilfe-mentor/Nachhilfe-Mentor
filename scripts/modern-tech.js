// Modern Tech JavaScript for Nachhilfe Mentor

class ModernTechWebsite {
    constructor() {
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupScrollAnimations();
        this.setupCounterAnimations();
        this.setupParticleSystem();
        this.setupMobileMenu();
        this.setupSmoothScrolling();
        this.setupIntersectionObserver();
    }



    // Navigation
    setupNavigation() {
        const navbar = document.getElementById('navbar');
        const navLinks = document.querySelectorAll('.nav-link');
        
        // Navbar scroll effect
        window.addEventListener('scroll', () => {
            if (window.scrollY > 100) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
        
        // Active link highlighting
        const sections = document.querySelectorAll('section[id]');
        
        window.addEventListener('scroll', () => {
            const scrollPos = window.scrollY + 100;
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                const sectionId = section.getAttribute('id');
                
                if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
                    navLinks.forEach(link => {
                        link.classList.remove('active');
                        if (link.getAttribute('href') === `#${sectionId}`) {
                            link.classList.add('active');
                        }
                    });
                }
            });
        });
    }

    // Mobile Menu
    setupMobileMenu() {
        const mobileToggle = document.getElementById('mobile-menu-toggle');
        const navMenu = document.getElementById('nav-menu');
        
        mobileToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            mobileToggle.classList.toggle('active');
        });
        
        // Close menu when clicking on a link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                mobileToggle.classList.remove('active');
            });
        });
    }

    // Counter Animations
    setupCounterAnimations() {
        const counters = document.querySelectorAll('.stat-number');
        
        const animateCounter = (counter) => {
            const target = parseInt(counter.getAttribute('data-count'));
            const duration = 2000;
            const step = target / (duration / 16);
            let current = 0;
            
            const updateCounter = () => {
                current += step;
                if (current >= target) {
                    counter.textContent = target.toLocaleString();
                    return;
                }
                counter.textContent = Math.floor(current).toLocaleString();
                requestAnimationFrame(updateCounter);
            };
            
            updateCounter();
        };
        
        // Trigger counters when they come into view
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    counterObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        counters.forEach(counter => {
            counterObserver.observe(counter);
        });
    }

    // Particle System
    setupParticleSystem() {
        const particleContainer = document.querySelector('.floating-particles');
        if (!particleContainer) return;
        
        const createParticle = () => {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.cssText = `
                position: absolute;
                width: 4px;
                height: 4px;
                background: rgba(102, 126, 234, 0.6);
                border-radius: 50%;
                pointer-events: none;
                animation: particle-float ${Math.random() * 3 + 2}s linear infinite;
                left: ${Math.random() * 100}%;
                top: 100%;
                opacity: 0;
            `;
            
            particleContainer.appendChild(particle);
            
            // Remove particle after animation
            setTimeout(() => {
                if (particle.parentNode) {
                    particle.parentNode.removeChild(particle);
                }
            }, 5000);
        };
        
        // Create particles periodically
        setInterval(createParticle, 300);
        
        // Add particle animation CSS
        if (!document.getElementById('particle-styles')) {
            const style = document.createElement('style');
            style.id = 'particle-styles';
            style.textContent = `
                @keyframes particle-float {
                    0% {
                        transform: translateY(0) translateX(0);
                        opacity: 0;
                    }
                    10% {
                        opacity: 1;
                    }
                    90% {
                        opacity: 1;
                    }
                    100% {
                        transform: translateY(-100vh) translateX(${Math.random() * 200 - 100}px);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // Scroll Animations
    setupScrollAnimations() {
        const animatedElements = document.querySelectorAll('.feature-card, .benefit-card, .process-step');
        
        const scrollObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.1 });
        
        animatedElements.forEach(element => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(50px)';
            element.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
            scrollObserver.observe(element);
        });
    }

    // Smooth Scrolling
    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    const offsetTop = target.offsetTop - 80;
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }

    // Intersection Observer for advanced animations
    setupIntersectionObserver() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);
        
        // Observe elements that should animate in
        document.querySelectorAll('.hero-visual, .phone-mockup, .devices-showcase').forEach(el => {
            observer.observe(el);
        });
    }

    // Utility method for creating glitch effect
    createGlitchEffect(element) {
        const glitchClone = element.cloneNode(true);
        glitchClone.classList.add('glitch-clone');
        element.parentNode.insertBefore(glitchClone, element);
        
        setTimeout(() => {
            glitchClone.remove();
        }, 200);
    }

    // Method to add hover effects to buttons
    enhanceButtons() {
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                btn.style.transform = 'translateY(-2px) scale(1.02)';
            });
            
            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translateY(0) scale(1)';
            });
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Ensure body can scroll
    document.body.style.overflow = 'auto';
    document.body.style.overflowX = 'hidden';

    new ModernTechWebsite();
});

// Add some additional CSS for animations
const additionalStyles = `
    .animate-in {
        animation: slideInUp 0.8s ease-out forwards;
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(50px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .nav-link.active {
        color: var(--primary-color) !important;
    }
    
    .nav-link.active::after {
        width: 100% !important;
    }
    
    .mobile-menu-toggle.active span:nth-child(1) {
        transform: rotate(45deg) translate(5px, 5px);
    }
    
    .mobile-menu-toggle.active span:nth-child(2) {
        opacity: 0;
    }
    
    .mobile-menu-toggle.active span:nth-child(3) {
        transform: rotate(-45deg) translate(7px, -6px);
    }
    
    @media (max-width: 768px) {
        .nav-menu.active {
            display: flex;
            position: fixed;
            top: 80px;
            left: 0;
            right: 0;
            background: rgba(10, 10, 10, 0.95);
            backdrop-filter: blur(20px);
            flex-direction: column;
            padding: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
    }
`;

// Inject additional styles
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);


