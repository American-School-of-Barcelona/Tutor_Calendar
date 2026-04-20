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

function isBookingStillUpcoming(booking) {
    const end = new Date(booking.end_time);
    return end > new Date();
}

// Render booking list
function renderBookings(bookings) {
    const container = document.getElementById('bookings-list');
    const loading = document.getElementById('bookings-loading');
    const empty = document.getElementById('bookings-empty');

    bookings = (bookings || []).filter(isBookingStillUpcoming);

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
                <div class="student-booking-item" data-booking-id="${booking.id}" data-start-time="${booking.start_time}" data-price-eur="${booking.price_eur || ''}">
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
                        <button type="button" class="student-booking-cancel-btn" data-id="${booking.id}">
                            Cancel Booking
                        </button>
                    </div>
                ` : `
                `}
            </div>
        `;
    }).join('');
}

// Handle cancel booking
function isWithin24h(isoStart) {
    const start = new Date(isoStart);
    const now = new Date();
    const diffMs = start - now;
    return diffMs > 0 && diffMs <= 24 * 60 * 60 * 1000;
}

function notifyCalendarsBookingChanged() {
    try {
        localStorage.setItem('tutor_calendar_invalidate', String(Date.now()));
    } catch (e) {
        /* ignore private mode */
    }
}

function handleCancelBooking(event) {
    const btn = event.target.closest('.student-booking-cancel-btn');
    if (!btn) {
        return;
    }
    const bookingId = btn.getAttribute('data-id');
    const bookingItem = btn.closest('.student-booking-item');
    if (!bookingId || !bookingItem) {
        return;
    }
    const startTime = bookingItem.getAttribute('data-start-time');
    const priceEur = bookingItem.getAttribute('data-price-eur') || '0';
    const within24h = startTime && isWithin24h(startTime);
    const msg = within24h
        ? 'This lesson is within 24 hours. Cancelling may result in the full lesson fee (' + priceEur + '€) being charged. Do you still want to cancel?'
        : 'Are you sure you want to cancel this booking?';
    if (!confirm(msg)) {
        return;
    }

    fetch(`/student/bookings/${bookingId}/cancel`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin',
    })
    .then((response) => {
        if (!response.ok) {
            return response.json().then((body) => Promise.reject(body));
        }
        return response.json();
    })
    .then((data) => {
        if (data.success) {
            if (data.within_24h) {
                alert('Booking cancelled. Cancelling within 24 hours of the lesson may result in the lesson fee being charged.');
            }
            notifyCalendarsBookingChanged();
            bookingItem.remove();
            loadBookings();
        } else {
            alert(data.error || 'Failed to cancel booking');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        const msg = (error && error.error) || error.message || 'Network error. Please try again.';
        alert(msg);
    });
}

// Load bookings from API
function loadBookings() {
    fetch('/api/student/bookings', { credentials: 'same-origin' })
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
    const list = document.getElementById('bookings-list');
    if (list) {
        list.addEventListener('click', handleCancelBooking);
    }
    loadBookings();
    setInterval(loadBookings, 30000);
});