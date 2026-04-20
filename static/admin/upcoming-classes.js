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

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Render classes list (similar to booking approvals)
function renderClasses(bookings) {
    const container = document.getElementById('classes-list');
    const loading = document.getElementById('classes-loading');
    const empty = document.getElementById('classes-empty');
    
    loading.style.display = 'none';
    
    if (bookings.length === 0) {
        empty.style.display = 'block';
        container.innerHTML = '';
        return;
    }
    
    empty.style.display = 'none';
    
    container.innerHTML = bookings.map(booking => `
            <div class="booking-item" data-booking-id="${booking.id}" data-start-time="${booking.start_time}" data-price-eur="${booking.price_eur || ''}">
            <div class="booking-item-info">
                <div class="booking-item-header">
                    <h3 class="booking-student-name">${escapeHtml(booking.student_name || 'Unknown Student')}</h3>
                    <span class="booking-student-email">${escapeHtml(booking.student_email || '')}</span>
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
                </div>
            </div>
            
            <div class="booking-item-actions">
                <button type="button" class="booking-action-btn booking-action-cancel" data-id="${booking.id}" onclick="handleCancelClassFromButton(this)">
                    Cancel Class
                </button>
            </div>
        </div>
    `).join('');
    
    // Clicks handled by document listener (see DOMContentLoaded)
}

// Handle cancel class
function isWithin24h(isoStart) {
    const start = new Date(isoStart);
    const now = new Date();
    const diffMs = start - now;
    return diffMs > 0 && diffMs <= 24 * 60 * 60 * 1000;
}

function handleCancelClassFromButton(btn) {
    handleCancelClass({ currentTarget: btn });
}

function handleCancelClass(event) {
    const btn = event.currentTarget;
    const bookingId = btn.getAttribute('data-id');
    const bookingItem = btn.closest('.booking-item');
    if (!bookingId || !bookingItem) {
        console.error('Cancel: missing booking id or row', { bookingId, bookingItem });
        return;
    }

    const startTime = bookingItem.getAttribute('data-start-time');
    const priceEur = bookingItem.getAttribute('data-price-eur') || '0';
    const within24h = startTime && isWithin24h(startTime);
    const msg = within24h
        ? 'This class is within 24 hours. The student may still be charged (' + priceEur + '€). Cancel anyway? The student will be notified.'
        : 'Are you sure you want to cancel this class? The student will be notified.';
    if (!confirm(msg)) {
        return;
    }

    btn.disabled = true;

    fetch(`/admin/bookings/${bookingId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin'
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                if (data.within_24h) {
                    alert('Class cancelled. Cancelling within 24 hours may result in the lesson fee being charged.');
                }
                bookingItem.style.opacity = '0.5';
                bookingItem.style.pointerEvents = 'none';
                setTimeout(() => loadClasses(), 500);
            } else {
                alert(data.error || 'Failed to cancel class');
                btn.disabled = false;
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('Network error. Please try again.');
            btn.disabled = false;
        });
}

// Load upcoming classes
function loadClasses() {
    fetch('/api/admin/upcoming-classes')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderClasses(data.bookings);
            } else {
                console.error('Failed to load classes:', data.error);
                document.getElementById('classes-loading').textContent = 'Error loading classes. Please refresh.';
            }
        })
        .catch(error => {
            console.error('Error loading classes:', error);
            document.getElementById('classes-loading').textContent = 'Error loading classes. Please refresh.';
        });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadClasses();
});