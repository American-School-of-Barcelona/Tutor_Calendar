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
    
    container.innerHTML = bookings.map(booking => `
        <div class="booking-item" data-booking-id="${booking.id}">
            <div class="booking-item-info">
                <div class="booking-item-header">
                    <h3 class="booking-student-name">${escapeHtml(booking.student_name)}</h3>
                    <span class="booking-student-email">${escapeHtml(booking.student_email)}</span>
                </div>
                
                <div class="booking-item-details">
                    <div class="booking-detail">
                        <span class="booking-detail-label">Date:</span>
                        <span class="booking-detail-value">${formatDateTime(booking.start_time)}</span>
                    </div>
                    <div class="booking-detail">
                        <span class="booking-detail-label">Time:</span>
                        <span class="booking-detail-value">${formatTimeRange(booking.start_time, booking.end_time)}</span>
                    </div>
                    <div class="booking-detail">
                        <span class="booking-detail-label">Duration:</span>
                        <span class="booking-detail-value">${formatDuration(booking.lesson_minutes)}</span>
                    </div>
                    <div class="booking-detail">
                        <span class="booking-detail-label">Price:</span>
                        <span class="booking-detail-value booking-price">${booking.price_eur}€</span>
                    </div>
                    <div class="booking-detail">
                        <span class="booking-detail-label">Requested:</span>
                        <span class="booking-detail-value">${formatDateTime(booking.created_at)}</span>
                    </div>
                </div>
            </div>
            
            <div class="booking-item-actions">
                <button type="button" class="booking-action-btn booking-action-approve" data-action="approve" data-id="${booking.id}" onclick="handleBookingAction(this)">
                    ✓ Approve
                </button>
                <button type="button" class="booking-action-btn booking-action-deny" data-action="deny" data-id="${booking.id}" onclick="handleBookingAction(this)">
                    ✗ Deny
                </button>
            </div>
        </div>
    `).join('');
    
    // Clicks are handled by a single document-level listener (see DOMContentLoaded)
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (text == null || text === '') {
        return '';
    }
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Handle approve/deny action
function handleBookingAction(button) {
    const action = button.dataset.action;
    const bookingId = button.dataset.id;
    const bookingItem = button.closest('.booking-item');
    console.log('booking action click', { action, bookingId });

    if (!action || !bookingId || !bookingItem) {
        console.error('Missing action metadata', { action, bookingId });
        return;
    }

    if (!confirm(`Are you sure you want to ${action} this booking request?`)) {
        return;
    }

    const url = `/admin/bookings/${bookingId}/${action}`;
    button.disabled = true;

    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin'
    })
    .then(async (response) => {
        const contentType = response.headers.get('content-type') || '';
        const payload = contentType.includes('application/json')
            ? await response.json()
            : { success: false, error: await response.text() };

        if (!response.ok || !payload.success) {
            throw new Error(payload.error || `Failed to ${action} booking`);
        }

        bookingItem.style.opacity = '0.5';
        bookingItem.style.pointerEvents = 'none';
        setTimeout(() => loadBookings(), 300);
    })
    .catch(error => {
        console.error('Booking action failed:', error);
        alert(error.message || `Failed to ${action} booking`);
        button.disabled = false;
    });
}

// Load bookings from API
function loadBookings() {
    fetch('/api/admin/bookings?status=pending')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                try {
                    renderBookings(data.bookings);
                } catch (e) {
                    console.error(e);
                    alert('Could not render bookings: ' + e.message);
                }
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