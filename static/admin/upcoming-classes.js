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

// Render classes list
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
    
    container.innerHTML = bookings.map(booking => {
        return `
            <div class="booking-item">
                <div class="booking-item-info">
                    <div class="booking-item-header">
                        <h3 class="booking-student-name">${booking.student_name || 'Unknown Student'}</h3>
                        <p class="booking-student-email">${booking.student_email || ''}</p>
                    </div>
                    
                    <div class="booking-item-details">
                        <div class="booking-detail">
                            <span class="booking-detail-label">Date & Time:</span>
                            <span class="booking-detail-value">${formatDateTime(booking.start_time)}</span>
                        </div>
                        <div class="booking-detail">
                            <span class="booking-detail-label">Time Range:</span>
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
            </div>
        `;
    }).join('');
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