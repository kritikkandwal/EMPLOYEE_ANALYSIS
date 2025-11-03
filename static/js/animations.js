// Advanced animations for the productivity dashboard
class DashboardAnimations {
    constructor() {
        this.observer = null;
        this.init();
    }

    init() {
        this.initIntersectionObserver();
        this.initScrollAnimations();
        this.initHoverEffects();
        this.initLoadingAnimations();
    }

    initIntersectionObserver() {
        // Create intersection observer for scroll animations
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateOnScroll(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        // Observe all animatable elements
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            this.observer.observe(el);
        });
    }

    animateOnScroll(element) {
        const animationType = element.dataset.animation || 'fadeInUp';
        
        switch (animationType) {
            case 'fadeInUp':
                element.style.animation = `fadeInUp 0.6s ease-out forwards`;
                break;
            case 'fadeInLeft':
                element.style.animation = `fadeInLeft 0.6s ease-out forwards`;
                break;
            case 'fadeInRight':
                element.style.animation = `fadeInRight 0.6s ease-out forwards`;
                break;
            case 'scaleIn':
                element.style.animation = `scaleIn 0.5s ease-out forwards`;
                break;
            case 'slideInUp':
                element.style.animation = `slideInUp 0.6s ease-out forwards`;
                break;
        }

        // Remove observer after animation
        this.observer.unobserve(element);
    }

    initScrollAnimations() {
        // Add scroll-based parallax effects
        window.addEventListener('scroll', () => {
            this.handleParallax();
            this.handleNavbarScroll();
        });
    }

    handleParallax() {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('[data-parallax]');
        
        parallaxElements.forEach(element => {
            const speed = element.dataset.parallaxSpeed || 0.5;
            const yPos = -(scrolled * speed);
            element.style.transform = `translateY(${yPos}px)`;
        });
    }

    handleNavbarScroll() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }

    initHoverEffects() {
        // Add hover effects to interactive elements
        const hoverElements = document.querySelectorAll('.glass-card, .btn, .nav-link');
        
        hoverElements.forEach(element => {
            element.addEventListener('mouseenter', this.handleHoverEnter);
            element.addEventListener('mouseleave', this.handleHoverLeave);
        });

        // Special hover effects for productivity gauge
        const gauge = document.querySelector('.gauge');
        if (gauge) {
            gauge.addEventListener('mouseenter', () => {
                gauge.style.transform = 'scale(1.05)';
            });
            gauge.addEventListener('mouseleave', () => {
                gauge.style.transform = 'scale(1)';
            });
        }
    }

    handleHoverEnter(e) {
        const element = e.currentTarget;
        element.style.transform = 'translateY(-2px)';
        element.style.boxShadow = '0 12px 40px 0 rgba(0, 255, 255, 0.2)';
    }

    handleHoverLeave(e) {
        const element = e.currentTarget;
        element.style.transform = 'translateY(0)';
        element.style.boxShadow = '';
    }

    initLoadingAnimations() {
        // Add loading animations for charts and data
        this.animateProgressBars();
        this.animateCounters();
    }

    animateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-fill, .metric-fill');
        
        progressBars.forEach(bar => {
            const width = bar.style.width;
            bar.style.width = '0%';
            
            setTimeout(() => {
                bar.style.transition = 'width 1s ease-in-out';
                bar.style.width = width;
            }, 300);
        });
    }

    animateCounters() {
        const counters = document.querySelectorAll('[data-counter]');
        
        counters.forEach(counter => {
            const target = parseInt(counter.dataset.counter);
            const duration = 2000; // 2 seconds
            const step = target / (duration / 16); // 60fps
            let current = 0;
            
            const timer = setInterval(() => {
                current += step;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                counter.textContent = Math.round(current);
            }, 16);
        });
    }

    // Particle animation for background
    createParticleAnimation() {
        const particlesContainer = document.getElementById('particles');
        if (!particlesContainer) return;

        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.cssText = `
                position: absolute;
                width: 2px;
                height: 2px;
                background: var(--primary-glow);
                border-radius: 50%;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: floatParticle ${10 + Math.random() * 20}s linear infinite;
                animation-delay: ${Math.random() * 5}s;
                opacity: ${0.3 + Math.random() * 0.7};
            `;
            particlesContainer.appendChild(particle);
        }
    }

    // Notification animation
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Remove after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    getNotificationIcon(type) {
        const icons = {
            'info': 'info-circle',
            'success': 'check-circle',
            'warning': 'exclamation-triangle',
            'error': 'times-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Chart loading animation
    animateChartLoading(canvas) {
        const ctx = canvas.getContext('2d');
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        let angle = 0;

        function drawSpinner() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            ctx.beginPath();
            ctx.arc(centerX, centerY, 20, angle, angle + Math.PI / 2);
            ctx.strokeStyle = 'var(--primary-glow)';
            ctx.lineWidth = 3;
            ctx.stroke();
            
            angle += 0.1;
            if (angle > Math.PI * 2) {
                angle = 0;
            }
            
            requestAnimationFrame(drawSpinner);
        }

        drawSpinner();
    }
}

// CSS Keyframes for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes fadeInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes scaleIn {
        from {
            opacity: 0;
            transform: scale(0.8);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(100%);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes floatParticle {
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
            transform: translateY(-100vh) translateX(100px);
            opacity: 0;
        }
    }

    .animate-on-scroll {
        opacity: 0;
    }

    .navbar.scrolled {
        background: rgba(10, 10, 15, 0.95);
        backdrop-filter: blur(20px);
    }

    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--bg-card);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: var(--glass-shadow);
        transform: translateX(400px);
        transition: transform 0.3s ease;
        z-index: 10000;
        max-width: 300px;
    }

    .notification.show {
        transform: translateX(0);
    }

    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .notification-success {
        border-left: 4px solid var(--accent-glow);
    }

    .notification-warning {
        border-left: 4px solid #ffaa00;
    }

    .notification-error {
        border-left: 4px solid #ff4444;
    }

    .particle {
        pointer-events: none;
    }
`;
document.head.appendChild(style);

// Initialize animations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardAnimations = new DashboardAnimations();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardAnimations;
}