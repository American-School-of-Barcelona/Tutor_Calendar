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
        'pending': { class: 'status-pending', text: 'Pending Approval' },
        'accepted': { class: 'status-accepted', text: 'Confirmed' },
        'denied': { class: 'status-denied', text: 'Denied' },
        'cancelled': { class: 'status-cancelled', text: 'Cancelled' }
    };
    return statusMap[status] || { class: 'status-unknown', text: status };
}

// Render booking list
function renderBookings(bookings) {
    const container = document.getElementById('bookings-list');
    const loading = document.getElementById('bookings-loading');
    const empty = document.getElementById('bookings-empty');
    
    loading.style.display = 'none';
    
    if (bookings.length === 0) {
        empty.style.display = 'block';
        container.innerHTML = '';
        return;
    }
    
    empty.style.display = 'none';
    
    container.innerHTML = bookings.map(booking => {
        const statusInfo = getStatusDisplay(booking.status);
        const canCancel = booking.status === 'pending';
        
        return `
            <div class="student-booking-item" data-booking-id="${booking.id}">
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
                
                ${canCancel ? `
                    <div class="student-booking-actions">
                        <button class="student-booking-cancel-btn" data-id="${booking.id}">
                            Cancel Booking
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
    
    // Attach cancel event listeners
    container.querySelectorAll('.student-booking-cancel-btn').forEach(btn => {
        btn.addEventListener('click', handleCancelBooking);
    });
}

// Handle cancel booking
function handleCancelBooking(event) {
    const bookingId = event.target.getAttribute('data-id');
    const bookingItem = event.target.closest('.student-booking-item');
    
    if (!confirm('Are you sure you want to cancel this booking?')) {
        return;
    }
    
    fetch(`/student/bookings/${bookingId}/cancel`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bookingItem.style.opacity = '0.5';
            bookingItem.style.pointerEvents = 'none';
            setTimeout(() => {
                loadBookings();
            }, 500);
        } else {
            alert(data.error || 'Failed to cancel booking');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Network error. Please try again.');
    });
}

// Load bookings from API
function loadBookings() {
    fetch('/api/student/bookings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderBookings(data.bookings);
            } else {
                console.error('Failed to load bookings:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading bookings:', error);
            document.getElementById('bookings-loading').textContent = 'Error loading bookings. Please refresh.';
        });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadBookings();
});