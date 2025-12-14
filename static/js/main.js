// Main JavaScript file for AI Productivity Intelligence Dashboard

class ProductivityApp {
    constructor() {
        this.currentUser = null;
        this.dashboardData = null;
        this.init();
    }

    init() {
        this.initializeApp();
        this.setupEventListeners();
        // this.loadUserData();
        this.setupServiceWorker();
    }

    initializeApp() {
        // Set theme based on user preference or time of day
        this.setThemeBasedOnTime();
        
        // Initialize tooltips
        this.initTooltips();
        

        console.log('Productivity App Initialized');
    }

    setupEventListeners() {
        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Search functionality
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e));
        }

        // Notification buttons
        const notificationButtons = document.querySelectorAll('.nav-icon[title="Notifications"]');
        notificationButtons.forEach(btn => {
            btn.addEventListener('click', () => this.showNotifications());
        });

        // Form submissions
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        });

        // Responsive menu
        this.setupMobileMenu();

        // Real-time updates
        this.startRealTimeUpdates();
    }

    setThemeBasedOnTime() {
        const hour = new Date().getHours();
        const isDarkHours = hour < 6 || hour > 18; // 6 PM to 6 AM
        
        if (isDarkHours && !localStorage.getItem('theme')) {
            document.body.classList.add('dark-theme');
        }
        
        // Load saved theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.body.classList.toggle('dark-theme', savedTheme === 'dark');
        }
    }

    toggleTheme() {
        const isDark = document.body.classList.toggle('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        
        // Update theme toggle icon
        const themeIcon = document.querySelector('#theme-toggle i');
        if (themeIcon) {
            themeIcon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    initTooltips() {
        // Initialize tooltips for interactive elements
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', this.showTooltip);
            element.addEventListener('mouseleave', this.hideTooltip);
        });
    }

    showTooltip(e) {
        const tooltipText = e.currentTarget.dataset.tooltip;
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = tooltipText;
        
        document.body.appendChild(tooltip);
        
        // Position tooltip
        const rect = e.currentTarget.getBoundingClientRect();
        tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    }

    hideTooltip(e) {
        const tooltips = document.querySelectorAll('.tooltip');
        tooltips.forEach(tooltip => tooltip.remove());
    }

    
    updateAIInsights(insights) {
        const insightsContainer = document.querySelector('.ai-insights-card');
        if (!insightsContainer || !insights) return;

        // Update insights content
        const insightItems = insightsContainer.querySelectorAll('.insight-item');
        insightItems.forEach((item, index) => {
            const insight = insights[index];
            if (insight) {
                const textElement = item.querySelector('.insight-text p');
                if (textElement) {
                    textElement.textContent = insight.text;
                }
            }
        });
    }

    handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase();
        
        // Implement search functionality
        if (searchTerm.length > 2) {
            this.performSearch(searchTerm);
        }
    }

    async performSearch(searchTerm) {
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(searchTerm)}`);
            if (response.ok) {
                const results = await response.json();
                this.displaySearchResults(results);
            }
        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    displaySearchResults(results) {
        // Implement search results display
        console.log('Search results:', results);
    }

    showNotifications() {
        // Show notifications panel
        const notificationsPanel = document.createElement('div');
        notificationsPanel.className = 'notifications-panel';
        notificationsPanel.innerHTML = `
            <div class="notifications-header">
                <h3>Notifications</h3>
                <button class="close-notifications">&times;</button>
            </div>
            <div class="notifications-list">
                <!-- Notifications will be loaded here -->
            </div>
        `;

        document.body.appendChild(notificationsPanel);

        // Load notifications
        this.loadNotifications();
    }

    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications');
            if (response.ok) {
                const notifications = await response.json();
                this.displayNotifications(notifications);
            }
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    }

    displayNotifications(notifications) {
        const notificationsList = document.querySelector('.notifications-list');
        if (!notificationsList) return;

        notificationsList.innerHTML = notifications.map(notification => `
            <div class="notification-item ${notification.type}">
                <div class="notification-icon">
                    <i class="fas fa-${this.getNotificationIcon(notification.type)}"></i>
                </div>
                <div class="notification-content">
                    <p>${notification.message}</p>
                    <span class="notification-time">${notification.time}</span>
                </div>
            </div>
        `).join('');
    }

    getNotificationIcon(type) {
        const icons = {
            'info': 'info-circle',
            'success': 'check-circle',
            'warning': 'exclamation-triangle',
            'error': 'times-circle'
        };
        return icons[type] || 'bell';
    }

    setupMobileMenu() {
        const menuToggle = document.querySelector('.mobile-menu-toggle');
        const sidebar = document.querySelector('.sidebar');

        if (menuToggle && sidebar) {
            menuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('mobile-open');
            });
        }

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('mobile-open')) {
                if (!sidebar.contains(e.target) && !e.target.closest('.mobile-menu-toggle')) {
                    sidebar.classList.remove('mobile-open');
                }
            }
        });
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        
        try {
            const response = await fetch(form.action, {
                method: form.method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const result = await response.json();
                this.handleFormSuccess(form, result);
            } else {
                this.handleFormError(form, response);
            }
        } catch (error) {
            this.handleFormError(form, error);
        }
    }

    handleFormSuccess(form, result) {
        // Show success message
        if (window.dashboardAnimations) {
            window.dashboardAnimations.showNotification(result.message || 'Success!', 'success');
        }

        // Reset form if needed
        if (form.dataset.resetOnSuccess) {
            form.reset();
        }

        // Redirect if specified
        if (result.redirect) {
            window.location.href = result.redirect;
        }
    }

    handleFormError(form, error) {
        console.error('Form submission error:', error);
        
        if (window.dashboardAnimations) {
            window.dashboardAnimations.showNotification(
                'An error occurred. Please try again.',
                'error'
            );
        }
    }

    
    handleRealTimeData(data) {
        // Update UI with real-time data
        switch (data.type) {
            case 'productivity_update':
                this.updateRealTimeProductivity(data.payload);
                break;
            case 'notification':
                this.showRealTimeNotification(data.payload);
                break;
            case 'badge_earned':
                this.showBadgeEarned(data.payload);
                break;
        }
    }

    updateRealTimeProductivity(data) {
        // Update productivity metrics in real-time
        const scoreElement = document.querySelector('.gauge-score');
        if (scoreElement) {
            scoreElement.textContent = Math.round(data.score);
        }

        // Update charts
        if (window.productivityCharts) {
            window.productivityCharts.updateRealTimeData(data);
        }
    }

    showRealTimeNotification(notification) {
        if (window.dashboardAnimations) {
            window.dashboardAnimations.showNotification(
                notification.message,
                notification.type
            );
        }
    }

    showBadgeEarned(badge) {
        // Show badge earned animation
        const badgeAnimation = document.createElement('div');
        badgeAnimation.className = 'badge-earned-animation';
        badgeAnimation.innerHTML = `
            <div class="badge-popup">
                <div class="badge-icon">${badge.icon}</div>
                <h3>Badge Earned!</h3>
                <p>${badge.name}</p>
                <p class="badge-description">${badge.description}</p>
            </div>
        `;

        document.body.appendChild(badgeAnimation);

        // Remove after animation
        setTimeout(() => {
            badgeAnimation.remove();
        }, 5000);
    }

    setupServiceWorker() {
        // Register service worker for PWA functionality
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('SW registered: ', registration);
                })
                .catch(registrationError => {
                    console.log('SW registration failed: ', registrationError);
                });
        }
    }

    // Utility methods
    formatTime(minutes) {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
    }

    formatPercentage(value) {
        return `${Math.round(value)}%`;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// CSS for additional components
const additionalStyles = `
    .tooltip {
        position: absolute;
        background: var(--bg-dark);
        color: var(--text-primary);
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        border: 1px solid var(--glass-border);
        box-shadow: var(--glass-shadow);
        z-index: 1000;
        white-space: nowrap;
        pointer-events: none;
    }

    .notifications-panel {
        position: fixed;
        top: 0;
        right: 0;
        width: 400px;
        height: 100vh;
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border-left: 1px solid var(--glass-border);
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    }

    .notifications-panel.show {
        transform: translateX(0);
    }

    .notifications-header {
        padding: 1.5rem;
        border-bottom: 1px solid var(--glass-border);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .close-notifications {
        background: none;
        border: none;
        color: var(--text-primary);
        font-size: 1.5rem;
        cursor: pointer;
    }

    .notifications-list {
        padding: 1rem;
        overflow-y: auto;
        height: calc(100vh - 80px);
    }

    .notification-item {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 1rem;
        margin-bottom: 0.5rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        border-left: 3px solid transparent;
    }

    .notification-item.info {
        border-left-color: var(--primary-glow);
    }

    .notification-item.success {
        border-left-color: var(--accent-glow);
    }

    .notification-item.warning {
        border-left-color: #ffaa00;
    }

    .notification-item.error {
        border-left-color: #ff4444;
    }

    .notification-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .notification-item.info .notification-icon {
        background: rgba(0, 255, 255, 0.1);
        color: var(--primary-glow);
    }

    .notification-item.success .notification-icon {
        background: rgba(0, 255, 136, 0.1);
        color: var(--accent-glow);
    }

    .notification-content p {
        margin: 0 0 0.25rem 0;
        font-size: 0.875rem;
    }

    .notification-time {
        font-size: 0.75rem;
        color: var(--text-secondary);
    }

    .badge-earned-animation {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 10000;
    }

    .badge-popup {
        background: var(--bg-card);
        border: 2px solid var(--accent-glow);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0, 255, 136, 0.3);
        animation: badgePop 0.6s ease-out;
    }

    @keyframes badgePop {
        0% {
            transform: scale(0.5);
            opacity: 0;
        }
        70% {
            transform: scale(1.1);
        }
        100% {
            transform: scale(1);
            opacity: 1;
        }
    }

    .badge-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }

    .badge-popup h3 {
        margin-bottom: 0.5rem;
        color: var(--accent-glow);
    }

    .badge-description {
        color: var(--text-secondary);
        font-size: 0.875rem;
    }

    @media (max-width: 768px) {
        .notifications-panel {
            width: 100%;
        }
    }
`;

// Add styles to document
if (document.head) {
    const styleSheet = document.createElement('style');
    styleSheet.textContent = additionalStyles;
    document.head.appendChild(styleSheet);
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.productivityApp = new ProductivityApp();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProductivityApp;
}