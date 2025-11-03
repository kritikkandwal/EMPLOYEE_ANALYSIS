// Lenis smooth scroll implementation
import Lenis from 'https://cdn.jsdelivr.net/npm/lenis@1.0.45/+esm';

class SmoothScroll {
    constructor() {
        this.lenis = null;
        this.init();
    }

    init() {
        // Initialize Lenis smooth scroll
        this.lenis = new Lenis({
            duration: 1.2,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // Custom easing function
            direction: 'vertical',
            gestureDirection: 'vertical',
            smooth: true,
            smoothTouch: false,
            touchMultiplier: 2,
        });

        // Start RAF
        this.startScrollAnimation();

        // Add scroll events
        this.addScrollEvents();

        console.log('Smooth scroll initialized');
    }

    startScrollAnimation() {
        function raf(time) {
            this.lenis.raf(time);
            requestAnimationFrame(raf.bind(this));
        }
        requestAnimationFrame(raf.bind(this));
    }

    addScrollEvents() {
        // Update CSS variables based on scroll
        this.lenis.on('scroll', (e) => {
            this.handleScrollEffects(e);
        });

        // Add smooth scroll to anchor links
        document.querySelectorAll('a[href^="#"]').forEach(link => {
            link.addEventListener('click', (e) => {
                this.handleAnchorClick(e);
            });
        });
    }

    handleScrollEffects(e) {
        const scrollProgress = e.progress;
        
        // Update CSS custom property for scroll-based animations
        document.documentElement.style.setProperty('--scroll-progress', scrollProgress);

        // Parallax effects
        this.updateParallaxElements(scrollProgress);

        // Progress indicators
        this.updateProgressIndicators(scrollProgress);

        // Section animations
        this.triggerSectionAnimations(scrollProgress);
    }

    updateParallaxElements(progress) {
        const parallaxElements = document.querySelectorAll('[data-parallax]');
        
        parallaxElements.forEach(element => {
            const speed = element.dataset.parallaxSpeed || 0.5;
            const yPos = progress * 100 * speed;
            element.style.transform = `translateY(${yPos}px)`;
        });
    }

    updateProgressIndicators(progress) {
        const progressBars = document.querySelectorAll('.scroll-progress');
        
        progressBars.forEach(bar => {
            bar.style.width = `${progress * 100}%`;
        });
    }

    triggerSectionAnimations(progress) {
        const sections = document.querySelectorAll('section[data-animate]');
        
        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            const sectionTop = rect.top;
            const sectionHeight = rect.height;
            const windowHeight = window.innerHeight;

            // Calculate when section is in view
            const sectionProgress = 1 - (sectionTop + sectionHeight) / (windowHeight + sectionHeight);
            
            if (sectionProgress > 0 && sectionProgress < 1) {
                this.animateSection(section, sectionProgress);
            }
        });
    }

    animateSection(section, progress) {
        const animationType = section.dataset.animate;
        
        switch (animationType) {
            case 'fade':
                section.style.opacity = progress;
                break;
            case 'slide-up':
                section.style.transform = `translateY(${(1 - progress) * 50}px)`;
                section.style.opacity = progress;
                break;
            case 'scale':
                const scale = 0.8 + (progress * 0.2);
                section.style.transform = `scale(${scale})`;
                section.style.opacity = progress;
                break;
        }
    }

    handleAnchorClick(e) {
        e.preventDefault();
        
        const href = e.currentTarget.getAttribute('href');
        if (href === '#') return;

        const target = document.querySelector(href);
        if (target) {
            this.lenis.scrollTo(target, {
                offset: -80, // Account for fixed header
                duration: 1.5
            });
        }
    }

    // Public method to scroll to element
    scrollToElement(selector, options = {}) {
        const element = document.querySelector(selector);
        if (element) {
            this.lenis.scrollTo(element, {
                offset: options.offset || -80,
                duration: options.duration || 1.5
            });
        }
    }

    // Public method to scroll to top
    scrollToTop() {
        this.lenis.scrollTo(0, {
            duration: 1.2
        });
    }

    // Public method to update Lenis options
    updateOptions(options) {
        this.lenis.options = { ...this.lenis.options, ...options };
    }

    // Destroy method for cleanup
    destroy() {
        if (this.lenis) {
            this.lenis.destroy();
            this.lenis = null;
        }
    }
}

// CSS for scroll progress and other scroll-based elements
const scrollStyles = `
    .scroll-progress {
        position: fixed;
        top: 0;
        left: 0;
        width: 0%;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-glow), var(--accent-glow));
        z-index: 10000;
        transition: width 0.1s ease;
    }

    [data-parallax] {
        transition: transform 0.1s ease-out;
    }

    section[data-animate] {
        transition: all 0.6s ease-out;
    }
`;

// Add styles to document
if (document.head) {
    const styleSheet = document.createElement('style');
    styleSheet.textContent = scrollStyles;
    document.head.appendChild(styleSheet);
}

// Initialize smooth scroll when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.smoothScroll = new SmoothScroll();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SmoothScroll;
}