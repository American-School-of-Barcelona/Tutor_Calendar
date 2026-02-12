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

// Calculate time until class starts
function getTimeUntil(startIso) {
    const now = new Date();
    const start = new Date(startIso);
    const diff = start - now;
    
    if (diff <= 0) {
        return 'Started';
    }
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (days > 0) {
        return `${days}d ${hours}h`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

// Get status badge class and text
function getStatusDisplay(status) {
    const statusMap = {
        'pending': { class: 'status-pending', text: 'Pending Approval' },
        'accepted': { class: 'status-accepted', text: 'Confirmed' },
        'denied': { class: 'status-denied', text: 'Denied' },
        'cancelled': { class: 'status-cancelled', text: 'Cancelled' }
    };
    return statusMap[status] || { class: 'status-unknown', text: status };
}

// Render upcoming classes with countdown
function renderUpcoming(bookings) {
    const container = document.getElementById('upcoming-list');
    const loading = document.getElementById('upcoming-loading');
    const empty = document.getElementById('upcoming-empty');
    
    loading.style.display = 'none';
    
    if (bookings.length === 0) {
        empty.style.display = 'block';
        container.innerHTML = '';
        return;
    }
    
    empty.style.display = 'none';
    
    container.innerHTML = bookings.map(booking => {
        const statusInfo = getStatusDisplay(booking.status);
        const timeUntil = getTimeUntil(booking.start_time);
        
        return `
            <div class="student-booking-item">
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
                        <div class="student-booking-detail">
                            <span class="student-booking-detail-label">Starts in:</span>
                            <span class="student-booking-detail-value countdown-timer" data-start="${booking.start_time}">${timeUntil}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Update countdown timers every minute
    updateCountdowns();
    setInterval(updateCountdowns, 60000);
}

// Update countdown timers
function updateCountdowns() {
    document.querySelectorAll('.countdown-timer').forEach(timer => {
        const startIso = timer.getAttribute('data-start');
        timer.textContent = getTimeUntil(startIso);
    });
}

// Render past classes
function renderPast(bookings) {
    const container = document.getElementById('past-list');
    const loading = document.getElementById('past-loading');
    const empty = document.getElementById('past-empty');
    
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

// Load upcoming classes
function loadUpcoming() {
    fetch('/api/student/bookings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderUpcoming(data.bookings);
            } else {
                console.error('Failed to load upcoming classes:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading upcoming classes:', error);
            document.getElementById('upcoming-loading').textContent = 'Error loading classes. Please refresh.';
        });
}

// Load past classes
function loadPast() {
    fetch('/api/student/history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderPast(data.bookings);
            } else {
                console.error('Failed to load past classes:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading past classes:', error);
            document.getElementById('past-loading').textContent = 'Error loading classes. Please refresh.';
        });
}

// Tab switching
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.classes-tab-btn');
    const sections = document.querySelectorAll('.classes-section');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Update button states
            tabButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update section visibility
            sections.forEach(s => s.style.display = 'none');
            document.getElementById(`${targetTab}-classes`).style.display = 'block';
            
            // Load data if needed
            if (targetTab === 'upcoming') {
                loadUpcoming();
            } else if (targetTab === 'past') {
                loadPast();
            }
        });
    });
    
    // Load initial data
    loadUpcoming();
});