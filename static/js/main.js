/**
 * Main JavaScript - Global functionality
 */

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', () => {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Check authentication status
    checkAuth();
    
    // Update notification count
    if (document.getElementById('notification-count')) {
        updateNotificationCount();
    }
});

/**
 * Check if user is authenticated
 */
async function checkAuth() {
    try {
        const response = await fetch('/auth/check');
        const data = await response.json();
        
        if (!data.success && !window.location.pathname.includes('/auth/')) {
            window.location.href = '/auth/login';
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}

/**
 * Update notification count in navbar
 */
async function updateNotificationCount() {
    try {
        const data = await apiCall('/notifications/unread-count');
        const badge = document.getElementById('notification-count');
        
        if (badge && data.count > 0) {
            badge.textContent = data.count;
            badge.classList.remove('hidden');
        } else if (badge) {
            badge.classList.add('hidden');
        }
    } catch (error) {
        console.error('Failed to update notification count:', error);
    }
}
