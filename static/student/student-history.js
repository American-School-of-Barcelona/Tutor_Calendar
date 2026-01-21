// Format datetime for display
function formatDateTime(isoString) {
    const date = new Date(isoString);
    const options = { 
        weekday: 'short', 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    };
    return date.toLocaleDateString('en-US', options);
}

// Format time range for display
function formatTimeRange(startIso, endIso) {
    const start = new Date(startIso);
    const end = new Date(endIso);
    
    const formatTime = (date) => {
        let hours = date.getHours();
        const minutes = date.getMinutes();
        const period = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        if (hours === 0) hours = 12;
        const minsStr = minutes.toString().padStart(2, '0');
        return `${hours}:${minsStr} ${period}`;
    };
    
    return `${formatTime(start)} - ${formatTime(end)}`;
}

// Format duration for display
function formatDuration(minutes) {
    const hours = Math.floor(minutes / 60);
    return `${hours}h`;
}

// Get status badge class and text
function getStatusDisplay(status) {
    const statusMap = {
        'pending': { class: 'status-pending', text: 'Pending' },
        'accepted': { class: 'status-accepted', text: 'Completed' },
        'denied': { class: 'status-denied', text: 'Denied' },
        'cancelled': { class: 'status-cancelled', text: 'Cancelled' }
    };
    return statusMap[status] || { class: 'status-unknown', text: status };
}

// Render history list
function renderHistory(bookings) {
    const container = document.getElementById('history-list');
    const loading = document.getElementById('history-loading');
    const empty = document.getElementById('history-empty');
    
    loading.style.display = 'none';
    
    if (bookings.length === 0) {
        empty.style.display = 'block';
        container.innerHTML = '';
        return;
    }
    
    empty.style.display = 'none';
    
    container.innerHTML = bookings.map(booking => {
        const statusInfo = getStatusDisplay(booking.status);
        
        return `
            <div class="student-booking-item student-booking-item-history">
                <div class="student-booking-info">
                    <div class="student-booking-header">
                        <h3 class="student-booking-date">${formatDateTime(booking.start_time)}</h3>
                        <span class="booking-status-badge ${statusInfo.class}">${statusInfo.text}</span>
                    </div>
                    
                    <div class="student-booking-details">
                        <div class="student-booking-detail">
                            <span class="student-booking-detail-label">Time:</span>
                            <span class="student-booking-detail-value">${formatTimeRange(booking.start_time, booking.end_time)}</span>
                        </div>
                        <div class="student-booking-detail">
                            <span class="student-booking-detail-label">Duration:</span>
                            <span class="student-booking-detail-value">${formatDuration(booking.lesson_minutes)}</span>
                        </div>
                        <div class="student-booking-detail">
                            <span class="student-booking-detail-label">Price:</span>
                            <span class="student-booking-detail-value student-booking-price">${booking.price_eur}€</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Load history from API
function loadHistory() {
    fetch('/api/student/history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderHistory(data.bookings);
            } else {
                console.error('Failed to load history:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading history:', error);
            document.getElementById('history-loading').textContent = 'Error loading history. Please refresh.';
        });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadHistory();
});