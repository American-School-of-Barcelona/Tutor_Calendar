const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];


const DAY_START_HOUR = 8;      // 8:00 AM
const DAY_END_HOUR = 20;       // 8:00 PM
const SLOT_INTERVAL_MINUTES = 15;

function generateTimeSlots() {
    const slots = [];
    const startMinutes = DAY_START_HOUR * 60;
    const endMinutes = DAY_END_HOUR * 60;

    for (let minutes = startMinutes; minutes < endMinutes; minutes += SLOT_INTERVAL_MINUTES) {
        const hour24 = Math.floor(minutes / 60);
        const mins = minutes % 60;

        const period = hour24 >= 12 ? 'PM' : 'AM';
        let hour12 = hour24 % 12;
        if (hour12 === 0) hour12 = 12;

        const minsStr = mins.toString().padStart(2, '0');
        slots.push(`${hour12}:${minsStr} ${period}`);
    }

    return slots;
}

const timeSlots = generateTimeSlots();

let currentWeekStart = getCurrentWeekStart();

function getCurrentWeekStart() {
    const today = new Date();
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(today.setDate(diff));
    monday.setHours(0, 0, 0, 0);
    return monday;
}

function getWeekDates(weekStart) {
    const dates = [];
    for (let i = 0; i < 7; i++) {
        const date = new Date(weekStart);
        date.setDate(weekStart.getDate() + i);
        dates.push(date);
    }
    return dates;
}

function formatDate(date) {
    const day = date.getDate();
    const suffix = getDaySuffix(day);
    return `${day}${suffix}`;
}

function getDaySuffix(day) {
    if (day > 3 && day < 21) return 'th';
    switch (day % 10) {
        case 1: return 'st';
        case 2: return 'nd';
        case 3: return 'rd';
        default: return 'th';
    }
}

function formatMonthYear(weekStart) {
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December'];
    const month = months[weekStart.getMonth()];
    const year = weekStart.getFullYear();
    return `${month} ${year}`;
}

function parseTime(timeStr) {
    const [time, period] = timeStr.split(' ');
    const [hours, minutes] = time.split(':').map(Number);
    let hour24 = hours;
    if (period === 'PM' && hours !== 12) hour24 = hours + 12;
    if (period === 'AM' && hours === 12) hour24 = 0;
    return { hours: hour24, minutes: minutes || 0 };
}

function isPastSlot(date, timeStr) {
    const now = new Date();
    const slotTime = parseTime(timeStr);
    const slotDate = new Date(date);
    slotDate.setHours(slotTime.hours, slotTime.minutes, 0, 0);
    return slotDate < now;
}

function renderCalendar() {
    const weekDates = getWeekDates(currentWeekStart);
    const headerRow = document.getElementById('calendar-header');
    const calendarBody = document.getElementById('calendar-body');
    
    headerRow.innerHTML = '';
    calendarBody.innerHTML = '';
    
    const emptyHeader = document.createElement('th');
    headerRow.appendChild(emptyHeader);
    
    weekDates.forEach((date, index) => {
        const dayName = daysOfWeek[index];
        const dateStr = formatDate(date);
        const headerCell = document.createElement('th');
        headerCell.textContent = `${dayName} - ${dateStr}`;
        headerRow.appendChild(headerCell);
    });
    
    timeSlots.forEach(time => {
        const timeRow = document.createElement('tr');
        
        const timeCell = document.createElement('th');
        timeCell.setAttribute('scope', 'row');
        timeCell.textContent = time;
        timeRow.appendChild(timeCell);
        
        weekDates.forEach((date, dayIndex) => {
            const dayCell = document.createElement('td');
            const dayName = daysOfWeek[dayIndex];
            const dateStr = date.toISOString().split('T')[0];
            
            dayCell.setAttribute('data-day', dayName);
            dayCell.setAttribute('data-time', time);
            dayCell.setAttribute('data-date', dateStr);
            
            if (isPastSlot(date, time)) {
                dayCell.classList.add('past-slot');
                dayCell.style.cursor = 'not-allowed';
            }
            
            timeRow.appendChild(dayCell);
        });
        
        calendarBody.appendChild(timeRow);
    });
    
    document.getElementById('week-display').textContent = formatMonthYear(currentWeekStart);
    checkPastSlots();

    loadBookingColors();
}

function checkPastSlots() {
    const now = new Date();
    const cells = document.querySelectorAll('#calendar td');
    
    cells.forEach(cell => {
        const dateStr = cell.getAttribute('data-date');
        const timeStr = cell.getAttribute('data-time');
        
        if (dateStr && timeStr) {
            const [year, month, day] = dateStr.split('-').map(Number);
            const slotTime = parseTime(timeStr);
            const slotDate = new Date(year, month - 1, day, slotTime.hours, slotTime.minutes, 0, 0);
            
            if (slotDate < now) {
                cell.classList.add('past-slot');
                cell.style.cursor = 'not-allowed';
            }
        }
    });
}

async function loadBookingColors() {
    try {
        const weekStartISO = currentWeekStart.toISOString();
        const response = await fetch(`/api/calendar/bookings?week_start=${weekStartISO}`);
        const data = await response.json();
        
        if (data.success && data.bookings) {
            applyBookingColors(data.bookings);
        }
    } catch (error) {
        console.error('Error loading booking colors:', error);
    }
}

function applyBookingColors(bookings) {
    const cells = document.querySelectorAll('#calendar td[data-date][data-time]');
    
    cells.forEach(cell => {
        const dateStr = cell.getAttribute('data-date');
        const timeStr = cell.getAttribute('data-time');
        
        if (!dateStr || !timeStr || cell.classList.contains('past-slot')) {
            return;
        }
        
        const slotTime = parseTime(timeStr);
        const [year, month, day] = dateStr.split('-').map(Number);
        const slotStart = new Date(year, month - 1, day, slotTime.hours, slotTime.minutes, 0, 0);
        const slotEnd = new Date(slotStart);
        slotEnd.setMinutes(slotEnd.getMinutes() + 15); // 15-minute slot
        
        // Check if this slot overlaps with any booking
        let slotStatus = 'available';
        
        for (const booking of bookings) {
            const bookingStart = new Date(booking.start_time);
            const bookingEnd = new Date(booking.end_time);
            
            // Check if slot overlaps with booking
            if (slotStart < bookingEnd && slotEnd > bookingStart) {
                if (booking.status === 'accepted') {
                    slotStatus = 'accepted';
                    break; // Accepted takes priority
                } else if (booking.status === 'pending' && slotStatus !== 'accepted') {
                    slotStatus = 'pending';
                }
            }
        }
        
        // Apply color class
        cell.classList.remove('slot-available', 'slot-pending', 'slot-accepted', 'slot-unavailable');
        
        if (slotStatus === 'available') {
            cell.classList.add('slot-available');
        } else if (slotStatus === 'pending') {
            cell.classList.add('slot-pending');
        } else if (slotStatus === 'accepted') {
            cell.classList.add('slot-accepted');
        }
    });
}

let currentBookingSlot = null;
let currentDuration = 120; // minutes, default 2 hours
const MIN_DURATION = 120; // 2 hours minimum
const MAX_DURATION = 240; // 4 hours maximum
const BASE_PRICE = 100; // euros for 2 hours
const PRICE_PER_HOUR = 50; // euros per additional hour

// Calculate price based on duration in minutes
function calculatePrice(minutes) {
    if (minutes < MIN_DURATION) return BASE_PRICE;
    const extraHours = (minutes - MIN_DURATION) / 60;
    return BASE_PRICE + (PRICE_PER_HOUR * extraHours);
}

// Format time for display (e.g., "11:00 AM - 1:00 PM")
function formatTimeRange(startTimeStr, durationMinutes) {
    const start = parseTime(startTimeStr);
    const startDate = new Date();
    startDate.setHours(start.hours, start.minutes, 0, 0);
    
    const endDate = new Date(startDate);
    endDate.setMinutes(endDate.getMinutes() + durationMinutes);
    
    const formatTime = (date) => {
        let hours = date.getHours();
        const minutes = date.getMinutes();
        const period = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        if (hours === 0) hours = 12;
        const minsStr = minutes.toString().padStart(2, '0');
        return `${hours}:${minsStr} ${period}`;
    };
    
    return `${formatTime(startDate)} - ${formatTime(endDate)}`;
}

// Open booking modal with selected slot
function openBookingModal(dateStr, timeStr, dayName) {
    currentBookingSlot = { dateStr, timeStr, dayName };
    currentDuration = MIN_DURATION;
    
    const slotDisplay = formatTimeRange(timeStr, currentDuration);
    document.getElementById('booking-slot-time').textContent = slotDisplay;
    document.getElementById('duration-display').textContent = '2h';
    document.getElementById('price-display').textContent = `${calculatePrice(currentDuration)}€`;
    
    document.getElementById('booking-modal').classList.add('active');
}

// Close booking modal
function closeBookingModal() {
    document.getElementById('booking-modal').classList.remove('active');
    document.getElementById('booking-error').style.display = 'none';
    currentBookingSlot = null;
    currentDuration = MIN_DURATION;
}

// Update duration display and price
function updateDurationDisplay() {
    const hours = Math.floor(currentDuration / 60);
    document.getElementById('duration-display').textContent = `${hours}h`;
    document.getElementById('price-display').textContent = `${calculatePrice(currentDuration)}€`;
    
    if (currentBookingSlot) {
        const slotDisplay = formatTimeRange(currentBookingSlot.timeStr, currentDuration);
        document.getElementById('booking-slot-time').textContent = slotDisplay;
    }
}

// Submit booking request
function submitBooking() {
    if (!currentBookingSlot) return;
    
    const { dateStr, timeStr } = currentBookingSlot;
    const slotTime = parseTime(timeStr);
    const [year, month, day] = dateStr.split('-').map(Number);
    
    const startDateTime = new Date(year, month - 1, day, slotTime.hours, slotTime.minutes, 0, 0);
    const endDateTime = new Date(startDateTime);
    endDateTime.setMinutes(endDateTime.getMinutes() + currentDuration);
    
    const bookingData = {
        start_time: startDateTime.toISOString(),
        lesson_minutes: currentDuration
    };
    
    fetch('/api/book-slot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(bookingData)
    })
    .then(response => response.json())
    .then(data => {
    
        if (data.success) {
            closeBookingModal();
            renderCalendar();
            showToast('Booking request submitted! Check your email for an approval notification.', 'success');
        } else {
            showToast(data.error || 'Failed to submit booking', 'error');
            document.getElementById('booking-error').textContent = data.error || 'Failed to submit booking';
            document.getElementById('booking-error').style.display = 'block';
        }
    })
    .catch(error => {
        document.getElementById('booking-error').textContent = 'Network error. Please try again.';
        document.getElementById('booking-error').style.display = 'block';
        console.error('Error:', error);
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const messageEl = document.createElement('div');
    messageEl.className = 'toast-message';
    messageEl.textContent = message;
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'toast-close';
    closeBtn.innerHTML = '×';
    closeBtn.onclick = () => removeToast(toast);
    
    toast.appendChild(messageEl);
    toast.appendChild(closeBtn);
    container.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        removeToast(toast);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function removeToast(toast) {
    toast.classList.add('fade-out');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

document.addEventListener('DOMContentLoaded', function() {
    renderCalendar();
    
    document.getElementById('prev-week').addEventListener('click', function() {
        currentWeekStart.setDate(currentWeekStart.getDate() - 7);
        renderCalendar();
    });
    
    document.getElementById('next-week').addEventListener('click', function() {
        currentWeekStart.setDate(currentWeekStart.getDate() + 7);
        renderCalendar();
    });
    
    // Calendar cell click handler - open modal instead of toggle
    const calendarTable = document.getElementById('calendar');
    calendarTable.addEventListener('click', function(event) {
        const clickedCell = event.target;
        
        if (clickedCell.tagName === 'TD' && !clickedCell.classList.contains('past-slot')) {
            const day = clickedCell.getAttribute('data-day');
            const time = clickedCell.getAttribute('data-time');
            const date = clickedCell.getAttribute('data-date');
            
            openBookingModal(date, time, day);
        }
    });
    
    // Modal controls
    document.getElementById('duration-decrease').addEventListener('click', function() {
        if (currentDuration > MIN_DURATION) {
            currentDuration -= 60;
            updateDurationDisplay();
        }
    });
    
    document.getElementById('duration-increase').addEventListener('click', function() {
        if (currentDuration < MAX_DURATION) {
            currentDuration += 60;
            updateDurationDisplay();
        }
    });
    
    document.getElementById('booking-cancel').addEventListener('click', closeBookingModal);
    document.getElementById('booking-confirm').addEventListener('click', submitBooking);
    
    // Close modal when clicking overlay
    document.querySelector('.booking-modal-overlay').addEventListener('click', closeBookingModal);
    
    setInterval(checkPastSlots, 60000);
});

let loadingOverlay = null;

function showLoading(message = 'Loading...') {
    if (loadingOverlay) return;
    
    loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    
    const content = document.createElement('div');
    content.className = 'loading-content';
    
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    
    const text = document.createElement('div');
    text.className = 'loading-text';
    text.textContent = message;
    
    content.appendChild(spinner);
    content.appendChild(text);
    loadingOverlay.appendChild(content);
    document.body.appendChild(loadingOverlay);
}

function hideLoading() {
    if (loadingOverlay) {
        loadingOverlay.remove();
        loadingOverlay = null;
    }
}

// Update submitBooking to show loading
function submitBooking() {
    if (!currentBookingSlot) return;
    
    showLoading('Submitting booking request...');
    
    // ... existing booking code ...
    
    fetch('/api/book-slot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(bookingData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            closeBookingModal();
            renderCalendar();
            showToast('Booking request submitted! Check your email for an approval notification.', 'success');
        } else {
            showToast(data.error || 'Failed to submit booking', 'error');
            document.getElementById('booking-error').textContent = data.error || 'Failed to submit booking';
            document.getElementById('booking-error').style.display = 'block';
        }
    })
    .catch(error => {
        hideLoading();
        showToast('Network error. Please try again.', 'error');
        document.getElementById('booking-error').textContent = 'Network error. Please try again.';
        document.getElementById('booking-error').style.display = 'block';
        console.error('Error:', error);
    });
}