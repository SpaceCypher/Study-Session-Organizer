/**
 * Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardData();
});

/**
 * Load all dashboard data
 */
async function loadDashboardData() {
    await Promise.all([
        loadStats(),
        loadInvitations(),
        loadUpcomingSessions(),
        loadNotifications()
    ]);
    
    // Refresh icons after content loads
    feather.replace();
}

/**
 * Load quick stats
 */
async function loadStats() {
    try {
        const data = await apiCall('/dashboard/stats');
        
        document.getElementById('stat-total').textContent = data.data.total_sessions;
        document.getElementById('stat-upcoming').textContent = data.data.upcoming_sessions;
        document.getElementById('stat-rating').textContent = data.data.avg_effectiveness.toFixed(1) + '/5.0';
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

/**
 * Load pending invitations
 */
async function loadInvitations() {
    const container = document.getElementById('invitations-container');
    const countEl = document.getElementById('invitations-count');
    
    try {
        const data = await apiCall('/dashboard/invitations');
        
        countEl.textContent = `${data.data.length} invite(s)`;
        
        if (data.data.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i data-feather="inbox" class="mx-auto mb-2"></i>
                    <p>No pending invitations</p>
                </div>
            `;
            return;
        }
        
        const invitationsHTML = data.data.map(invite => `
            <div class="border border-gray-200 rounded-lg p-4 hover:border-teal-500 transition duration-200">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex-1">
                        <h3 class="font-semibold text-gray-900">${invite.subject_name}</h3>
                        <p class="text-sm text-gray-600 mt-1">
                            <i data-feather="calendar" class="inline w-4 h-4"></i>
                            ${formatDate(invite.session_date)} at ${formatTime(invite.start_time)}
                        </p>
                        <p class="text-sm text-gray-600 mt-1">
                            <i data-feather="map-pin" class="inline w-4 h-4"></i>
                            ${invite.building || 'TBD'} ${invite.room_number || ''}
                        </p>
                    </div>
                    <span class="text-xs text-gray-500">${timeAgo(invite.sent_date)}</span>
                </div>
                <div class="flex gap-2">
                    <button onclick="acceptInvitation(${invite.session_id}, ${invite.notification_id})" class="flex-1 bg-teal-600 text-white px-3 py-2 rounded text-sm hover:bg-teal-700 transition duration-200">
                        Accept
                    </button>
                    <button onclick="declineInvitation(${invite.notification_id})" class="flex-1 bg-gray-200 text-gray-700 px-3 py-2 rounded text-sm hover:bg-gray-300 transition duration-200">
                        Decline
                    </button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = invitationsHTML;
        feather.replace();
        
    } catch (error) {
        console.error('Failed to load invitations:', error);
        container.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <p>Failed to load invitations</p>
            </div>
        `;
    }
}

/**
 * Accept session invitation
 */
async function acceptInvitation(sessionId, notificationId) {
    try {
        // Try to join the session
        try {
            await apiCall(`/sessions/${sessionId}/join`, 'POST');
            showToast('Joined session successfully!', 'success');
        } catch (joinError) {
            // If already joined, just mark as read
            if (joinError.message && joinError.message.includes('Already joined')) {
                showToast('You are already in this session', 'info');
            } else {
                throw joinError;
            }
        }
        
        // Mark notification as read
        await apiCall(`/notifications/${notificationId}/read`, 'PUT');
        loadDashboardData(); // Reload dashboard
    } catch (error) {
        showToast(error.message || 'Failed to accept invitation', 'error');
    }
}

/**
 * Decline session invitation
 */
async function declineInvitation(notificationId) {
    try {
        await apiCall(`/notifications/${notificationId}/read`, 'PUT');
        showToast('Invitation declined', 'success');
        loadDashboardData(); // Reload dashboard
    } catch (error) {
        showToast(error.message || 'Failed to decline invitation', 'error');
    }
}

/**
 * Load upcoming sessions
 */
async function loadUpcomingSessions() {
    const container = document.getElementById('upcoming-sessions-container');
    
    try {
        const data = await apiCall('/dashboard/upcoming');
        
        if (data.data.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i data-feather="calendar" class="mx-auto mb-2"></i>
                    <p>No upcoming sessions</p>
                    <a href="/sessions/browse" class="text-teal-600 hover:text-teal-700 text-sm">Browse sessions</a>
                </div>
            `;
            return;
        }
        
        const sessionsHTML = data.data.map(session => `
            <a href="/sessions/${session.session_id}" class="block border border-gray-200 rounded-lg p-4 hover:border-teal-500 hover:shadow-md transition duration-200">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h3 class="font-semibold text-gray-900">${session.subject_name}</h3>
                        <p class="text-sm text-gray-600 mt-1">
                            <i data-feather="calendar" class="inline w-4 h-4"></i>
                            ${formatDate(session.session_date)} at ${formatTime(session.start_time)}
                        </p>
                        <p class="text-sm text-gray-600 mt-1">
                            <i data-feather="map-pin" class="inline w-4 h-4"></i>
                            ${session.building || 'TBD'} ${session.room_number || ''}
                        </p>
                    </div>
                    <span class="px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(session.status)}">
                        ${session.status}
                    </span>
                </div>
                <div class="mt-2 flex items-center text-sm text-gray-500">
                    <i data-feather="users" class="inline w-4 h-4 mr-1"></i>
                    ${session.participant_count}/${session.max_participants} participants
                </div>
            </a>
        `).join('');
        
        container.innerHTML = sessionsHTML;
        feather.replace();
        
    } catch (error) {
        console.error('Failed to load upcoming sessions:', error);
        container.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <p>Failed to load sessions</p>
            </div>
        `;
    }
}

/**
 * Load recent notifications
 */
async function loadNotifications() {
    const container = document.getElementById('notifications-container');
    
    try {
        const data = await apiCall('/dashboard/notifications');
        
        if (data.data.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i data-feather="bell-off" class="mx-auto mb-2"></i>
                    <p>No notifications</p>
                </div>
            `;
            return;
        }
        
        const notificationsHTML = data.data.map(notification => `
            <div class="border-l-4 ${getNotificationBorderColor(notification.notification_type)} bg-gray-50 p-3 rounded">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <i data-feather="${getNotificationIcon(notification.notification_type)}" class="w-5 h-5 ${getNotificationIconColor(notification.notification_type)}"></i>
                    </div>
                    <div class="ml-3 flex-1">
                        <p class="text-sm text-gray-900 ${notification.read_status ? '' : 'font-semibold'}">
                            ${notification.message}
                        </p>
                        <p class="text-xs text-gray-500 mt-1">
                            ${timeAgo(notification.sent_date)}
                        </p>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = notificationsHTML;
        feather.replace();
        
    } catch (error) {
        console.error('Failed to load notifications:', error);
        container.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <p>Failed to load notifications</p>
            </div>
        `;
    }
}

/**
 * Get status badge color
 */
function getStatusColor(status) {
    const colors = {
        'Planned': 'bg-blue-100 text-blue-800',
        'Active': 'bg-green-100 text-green-800',
        'Completed': 'bg-gray-100 text-gray-800',
        'Cancelled': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
}

/**
 * Get notification border color
 */
function getNotificationBorderColor(type) {
    const colors = {
        'Session Invite': 'border-blue-500',
        'Reminder': 'border-yellow-500',
        'Cancellation': 'border-red-500',
        'Update': 'border-purple-500',
        'Feedback Request': 'border-green-500'
    };
    return colors[type] || 'border-gray-500';
}

/**
 * Get notification icon
 */
function getNotificationIcon(type) {
    const icons = {
        'Session Invite': 'mail',
        'Reminder': 'bell',
        'Cancellation': 'x-circle',
        'Update': 'refresh-cw',
        'Feedback Request': 'edit'
    };
    return icons[type] || 'bell';
}

/**
 * Get notification icon color
 */
function getNotificationIconColor(type) {
    const colors = {
        'Session Invite': 'text-blue-600',
        'Reminder': 'text-yellow-600',
        'Cancellation': 'text-red-600',
        'Update': 'text-purple-600',
        'Feedback Request': 'text-green-600'
    };
    return colors[type] || 'text-gray-600';
}
